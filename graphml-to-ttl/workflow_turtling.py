from hubs import *
import rdflib as rdf

namespaces = {
    'rdf': rdf.Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#'),
    'rdfs': rdf.Namespace('http://www.w3.org/2000/01/rdf-schema#'),
    'xsd': rdf.Namespace('http://www.w3.org/2001/XMLSchema#'),
    'xml': rdf.Namespace('http://www.w3.org/XML/1998/namespace'),
    'dbo': rdf.Namespace('https://dbpedia.org/ontology/'),
    'dct': rdf.Namespace('http://purl.org/dc/terms/'),
    'wf': rdf.Namespace('http://geographicknowledge.de/vocab/Workflow.rdf#'),
    'tools': rdf.Namespace('https://github.com/quangis/cct/blob/master/tools/tools.ttl#'),
    'repo': rdf.Namespace('https://example.com/#'),
    'data': rdf.Namespace('https://github.com/quangis/cct/blob/master/tools/data.ttl#'),
    'ccd': rdf.Namespace('http://geographicknowledge.de/vocab/CoreConceptData.rdf#'),
    'cct': rdf.Namespace('https://github.com/quangis/cct#')
}

class Workflow:
    def __init__(self, actions, graph):
        self.context = None
        self.actions = list(actions)
        self.artefacts = []
        self.graph = graph  # networkx graph

        # Check if the workflow has a single output
        input_candidates = set()
        output_candidates = set()
        for action in actions:
            input_candidates = input_candidates.union(set(action.inputs.values()))
            output_candidates = output_candidates.union(set(action.outputs.values()))
        inputs, outputs = derive_outer_nodes(input_candidates, output_candidates)
        if len(outputs) != 1:
            raise ValueError('Actions do not form a workflow with one final output')
        for action in actions:
            if set(action.inputs.values()) == set(inputs) and set(action.outputs.values()) == set(outputs):
                self.context = action
                self.actions.remove(action)

        for candidate in [*input_candidates, *output_candidates]:
            self.artefacts.append(Artefact(candidate, graph))

    # Reduces the actions in the workflow to the most specific set of actions
    def specify(self):
        actions = self.actions.copy()

        while actions:
            action = actions.pop()
            # Check if the action objects has components.
            if action.components.values():
                for component in action.components.values():
                    # Add more precise action
                    self.actions.append(Action(component, self.graph))
                    actions.append(Action(component, self.graph))
                # Remove coarse action
                if action in self.actions:
                    print('Removed: ', action)
                    self.actions.remove(action)

    # Reduces the actions in the workflow to the most general set of actions (excluding the context action)
    def generalize(self):
        actions = self.actions.copy()

        while actions:
            action = actions.pop()
            # Check if the action objects has components.
            if action.compositions.values():
                for composition in action.compositions.values():
                    # Add more precise action
                    self.actions.append(Action(composition, self.graph))
                    actions.append(Action(composition, self.graph))
                # Remove coarse action
                if action in self.actions:
                    print('Removed: ', action)
                    self.actions.remove(action)

    def to_rdf(self, file, context=None):

        rdf_graph = rdf.Graph()

        for prefix, namespace in namespaces.items():
            rdf_graph.bind(prefix, namespace)

        self.context_to_rdf(rdf_graph)
        self.actions_to_rdf(rdf_graph)
        self.artefacts_to_rdf(rdf_graph)

        def iterate_over_components(workflow, rdf_graph):
            for action in workflow.actions:
                if action.components:
                    components = [Action(component, action.graph) for component in action.components.values()]
                    sub_wf = Workflow([*components, action], action.graph)
                    sub_wf.context_to_rdf(rdf_graph)
                    sub_wf.actions_to_rdf(rdf_graph)
                    sub_wf.artefacts_to_rdf(rdf_graph)
                    iterate_over_components(sub_wf, rdf_graph)

        iterate_over_components(self, rdf_graph)

        # Write non-binary metadata
        with open(file, 'w') as f:
            authors = '# @Author(s): '
            if self.context is not None:
                for author in self.context.authors.items():
                    authors += self.graph.nodes[author[1]]['label'] + ', '
            f.write(authors + '\n')

        # Write binary-serialized data
        with open(file, 'ab') as f:
            rdf_graph.serialize(destination=f, format='n3')


    # Writes all triples related to the context to the passed rdf graph
    def context_to_rdf(self, rdf_graph):
        if self.context is None:
            raise ValueError("Tried to convert non-existent context to RDF")

        context_label = self.graph.nodes[self.context.node]['label']
        context_node = namespaces['tools'][context_label]

        # Workflow name
        rdf_graph.add((context_node,
                       rdf.RDF.type,
                       namespaces['wf']['Workflow']))

        # Context comments
        for comment in self.context.comments.items():
            rdf_graph.add((context_node,
                           rdf.RDFS.comment,
                           rdf.Literal(self.graph.nodes[comment[1]]['label'])))

        # Context subjects
        for expression in self.context.expressions.items():
            rdf_graph.add((context_node,
                           namespaces['dct']['subject'],
                           rdf.Literal(self.graph.nodes[expression[1]]['label'])))

        # Context abstracts
        for abstract in self.context.abstracts.items():
           rdf_graph.add((context_node,
                          namespaces['dbo']['abstract'],
                          rdf.Literal(self.graph.nodes[abstract[1]]['label'])))

        # Context Sources
        for source in self.context.inputs.items():
            rdf_graph.add((context_node,
                           namespaces['wf']['source'],
                           namespaces['data'][self.graph.nodes[source[1]]['label']]))

    # Writes all triples centred around actions to the passed rdf graph
    def actions_to_rdf(self, rdf_graph):

        # Add action nodes
        for action in self.actions:
            action_label = self.graph.nodes[action.node]['label']

            if self.context is not None:
                context_label = self.graph.nodes[self.context.node]['label']
                context_node = namespaces['tools'][context_label]
                # Add triple between context and action
                rdf_graph.add((context_node,
                               namespaces['wf']['edge'],
                               namespaces['data'][action.node]))

            # Add triple between context and action
            rdf_graph.add((namespaces['data'][action.node],
                           namespaces['wf']['applicationOf'],
                           namespaces['tools'][action_label]))

            # Add inputs
            for input in action.inputs.items():
                input_label = self.graph.nodes[input[1]]['label']
                rdf_graph.add((namespaces['data'][action.node],
                               namespaces['wf']['input' + str(int(input[0]) + 1)],
                               namespaces['data'][input_label]))

            # Add outputs
            for output in action.outputs.items():
                output_label = self.graph.nodes[output[1]]['label']
                rdf_graph.add((namespaces['data'][action.node],
                               namespaces['wf']['output'],
                               namespaces['data'][output_label]))

            # Add expressions
            for expression in action.expressions.items():
                expression_label = self.graph.nodes[expression[1]]['label']
                rdf_graph.add((namespaces['data'][action.node],
                               namespaces['cct']['expression'],
                               rdf.Literal([expression_label])))

            # Add comments
            for comment in action.comments.items():
                comment_label = self.graph.nodes[comment[1]]['label']
                rdf_graph.add((namespaces['data'][action.node],
                               rdf.RDFS.comment,
                               rdf.Literal(comment_label)))

            # Add labels
            for label in action.labels.items():
                label_label = self.graph.nodes[label[1]]['label']
                rdf_graph.add((namespaces['data'][action.node],
                               rdf.RDFS.label,
                               rdf.Literal(label_label)))

    # Writes all triples centred around artefacts to the passed rdf graph
    def artefacts_to_rdf(self, rdf_graph):
        for artefact in self.artefacts:
            artefact_label = self.graph.nodes[artefact.node]['label']

            # Add comments
            for comment in artefact.comments.items():
                comment_label = self.graph.nodes[comment[1]]['label']
                rdf_graph.add((namespaces['data'][artefact_label],
                               rdf.RDFS.comment,
                               rdf.Literal(comment_label)))

            # Add labels
            for label in artefact.labels.items():
                label_label = self.graph.nodes[label[1]]['label']
                rdf_graph.add((namespaces['data'][artefact_label],
                               rdf.RDFS.label,
                               rdf.Literal(label_label)))

            # Add signatures
            for signature in artefact.signatures.items():
                signature_label = self.graph.nodes[signature[1]]['label']
                rdf_graph.add((namespaces['data'][artefact_label],
                               rdf.RDF.type,
                               namespaces['ccd'][signature_label]))





