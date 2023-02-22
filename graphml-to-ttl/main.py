import networkx as nx
from rdflib import Graph, Namespace, RDF, RDFS, URIRef, BNode
from rdflib.term import Literal


class Action:
    def __init__(self, action_node=None, inputs=None, outputs=None, comments=None, expressions=None, labels=None):
        self.node = action_node
        self.inputs = inputs
        self.outputs = outputs
        self.comments = comments
        self.expressions = expressions
        self.labels = labels

    def __str__(self):
        statement = "Action: " + str(self.action) + "\n"
        statement += "Inputs: " + str(self.inputs) + "\n"
        statement += "Outputs: " + str(self.outputs) + "\n"
        statement += "Comments: " + str(self.comments) + "\n"
        statement += "expressions: " + str(self.expressions) + "\n"
        return statement


class Artefact:
    def __init__(self, artefact_node=None, inputs=None, outputs=None, comments=None, signatures=None, labels=None):
        self.node = artefact_node
        self.inputs = inputs
        self.outputs = outputs
        self.comments = comments
        self.signatures = signatures
        self.labels = labels
    def __str__(self):
        statement = "Artefact: " + str(self.action) + "\n"
        statement += "Inputs: " + str(self.inputs) + "\n"
        statement += "Outputs: " + str(self.outputs) + "\n"
        statement += "Comments: " + str(self.comments) + "\n"
        statement += "Signatures: " + str(self.signatures) + "\n"
        return statement


class Workflow:
    def __init__(self, name='', author='Unknown', comment='', subject='', abstract='.'):
        self.name = name
        self.author = author
        self.actions = set()
        self.artefacts = set()
        self.namespaces = {
             'rdf': Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#'),
             'rdfs': Namespace('http://www.w3.org/2000/01/rdf-schema#'),
             'xsd': Namespace('http://www.w3.org/2001/XMLSchema#'),
             'xml': Namespace('http://www.w3.org/XML/1998/namespace'),
             'dbo': Namespace('https://dbpedia.org/ontology/'),
             'dct': Namespace('http://purl.org/dc/terms/'),
             'wf': Namespace('http://geographicknowledge.de/vocab/Workflow.rdf#'),
             'tools': Namespace('https://github.com/quangis/cct/blob/master/tools/tools.ttl#'),
             'repo': Namespace('https://example.com/#'),
             'data': Namespace('https://github.com/quangis/cct/blob/master/tools/data.ttl#'),
             'ccd': Namespace('http://geographicknowledge.de/vocab/CoreConceptData.rdf#'),
             'cct': Namespace('https://github.com/quangis/cct#')
        } # TODO: Check namespaces
        self.comment = comment
        self.subject = subject
        self.abstract = abstract
        self.sources = set()

    def __str__(self):
        for action in self.actions:
            print(action)

    def update_metadata_from_networkx_dag(self, dag):
        self.sources = set()  # Empty existing sources

        for edge in dag.edges(data=True):

            # Get author, question, subject, abstract metadata by annotation edges
            if 'label' in edge[2]:
                if edge[2]['label'] == 'Author':
                    self.author = dag.nodes[edge[0]]['label']
                if edge[2]['label'] == 'Question':
                    self.comment = dag.nodes[edge[0]]['label']
                if edge[2]['label'] == 'Subject':
                    self.subject = dag.nodes[edge[0]]['label']
                if edge[2]['label'] == 'Abstract':
                    self.abstract = dag.nodes[edge[0]]['label']
                if edge[2]['label'] == 'Author':
                    self.name = dag.nodes[edge[1]]['label']

            # Get source labels by whether they are starting nodes
            if dag.nodes[edge[0]]['shape_type'] == 'parallelogram':
                if all(edge[0] != edge2[1] for edge2 in dag.edges):
                    self.sources.add(dag.nodes[edge[0]]['label'])

    def import_data_from_networkx_dag(self, dag):
        for node in dag.nodes(data=True):

            # Create artefacts from nodes
            if node[1]['shape_type'] in ['parallelogram']:
                artefact = node
                inputs = list()
                outputs = list()
                comments = list()
                signatures = list()
                labels = list()
                for edge in dag.edges:
                    # Let edges incoming from roundrectangles be inputs
                    if node[0] == edge[1] and dag.nodes[edge[0]]['shape_type'] == 'roundrectangle':
                        inputs.append((edge[0], dag.nodes[edge[0]]))
                    # Let edges outgoing to roundrectangles be outputs
                    if node[0] == edge[0] and dag.nodes[edge[1]]['shape_type'] == 'roundrectangle':
                        outputs.append((edge[1], dag.nodes[edge[1]]))
                    # Let edges incoming from fat arrows be comments
                    if node[0] == edge[1] and dag.nodes[edge[0]]['shape_type'] == 'fatarrow':
                        comments.append((edge[0], dag.nodes[edge[0]]))
                    if node[0] == edge[1] and dag.nodes[edge[0]]['shape_type'] == 'octagon':
                        signatures.append((edge[0], dag.nodes[edge[0]]))
                    if node[0] == edge[1] and dag.nodes[edge[0]]['shape_type'] == 'hexagon':
                        labels.append((edge[0], dag.nodes[edge[0]]))
                self.artefacts.add(Artefact(artefact, inputs, outputs, comments, signatures, labels))

            # Create actions from nodes
            if node[1]['shape_type'] == 'roundrectangle':
                action = node
                inputs = list()
                outputs = list()
                comments = list()
                expressions = list()
                labels = list()
                for edge in dag.edges:
                    # Let edges incoming from parallelograms be inputs
                    if node[0] == edge[1] and dag.nodes[edge[0]]['shape_type'] == 'parallelogram':
                        inputs.append((edge[0], dag.nodes[edge[0]]))
                    # Let edges outgoing to parallelograms be outputs
                    if node[0] == edge[0] and dag.nodes[edge[1]]['shape_type'] == 'parallelogram':
                        outputs.append((edge[1], dag.nodes[edge[1]]))
                    # Let edges incoming from fat arrows be comments
                    if node[0] == edge[1] and dag.nodes[edge[0]]['shape_type'] == 'fatarrow':
                        comments.append((edge[0], dag.nodes[edge[0]]))
                    if node[0] == edge[1] and dag.nodes[edge[0]]['shape_type'] == 'octagon':
                        expressions.append((edge[0], dag.nodes[edge[0]]))
                    if node[0] == edge[1] and dag.nodes[edge[0]]['shape_type'] == 'hexagon':
                        labels.append((edge[0], dag.nodes[edge[0]]))
                self.actions.add(Action(action, inputs, outputs, comments, expressions, labels))

    def update_namespaces(self, namespace_dict):
        self.namespaces.update(namespace_dict)

    def export_to_RDF(self, file):
        rdf_g = Graph()

        # Blank node namespace
        self.update_namespaces({'_': Namespace('#')})

        # Add namespaces to file
        for prefix, namespace in self.namespaces.items():
            rdf_g.bind(prefix, namespace)

        # Add workflow triples
        # Workflow name
        s = self.namespaces['repo'][self.name]
        p = BNode()
        o = self.namespaces['wf']['Workflow']
        rdf_g.add((s, p, o))

        # Question
        p = RDFS.comment
        o = Literal(self.comment)
        rdf_g.add((s, p, o))

        # Subject
        p = self.namespaces['dct']['subject']
        o = Literal(self.subject)
        rdf_g.add((s, p, o))

        # Abstract
        p = self.namespaces['dbo']['abstract']
        o = Literal(self.abstract)
        rdf_g.add((s, p, o))

        # Sources
        for source in self.sources:
            p = self.namespaces['wf']['source']
            #o = BNode(source)
            o = self.namespaces['data'][self.name + '_' + source]
            rdf_g.add((s, p, o))

        # Add actions
        for action in self.actions:
            p = self.namespaces['wf']['edge']
            o = self.namespaces['data'][self.name + '_' + str(action.node[0])]
            rdf_g.add((s, p, o))

        # Add action-specific triples to rdf_graph
        for action in self.actions:

            # Add tool node
            s = self.namespaces['data'][self.name + '_' + str(action.node[0])]
            p = self.namespaces['wf']['applicationOf']
            o = self.namespaces['tools'][action.node[1]['label']]
            rdf_g.add((s, p, o))

            # Add input nodes
            count = 0
            for input in action.inputs:
                count += 1
                p = self.namespaces['wf']['input'] + str(count)
                o = self.namespaces['data'][self.name + '_' + str(input[1]['label'])]
                rdf_g.add((s, p, o))

            # Add comments
            for comment in action.comments:
                p = RDFS.comment
                o = Literal(comment[1]['label'])
                rdf_g.add((s, p, o))

            # Add output nodes
            for output in action.outputs:
                p = self.namespaces['wf']['output']
                o = self.namespaces['data'][self.name + '_' + str(output[1]['label'])]
                rdf_g.add((s, p, o))

            # Add expressions
            for expression in action.expressions:
                p = self.namespaces['cct']['expression']
                o = Literal(expression[1]['label'])
                rdf_g.add((s, p, o))

            # Add labels
            for label in action.labels:
                p = RDFS.label
                o = Literal(label[1]['label'])
                rdf_g.add((s, p, o))

        # Add artefacts
        for artefact in self.artefacts:
            s = self.namespaces['data'][self.name + '_' + artefact.node[1]['label']]
            # Add artefact comments
            for comment in artefact.comments:
                p = RDFS.comment
                o = Literal(comment[1]['label'])
                rdf_g.add((s, p, o))
            # Add artefact comments
            for signature in artefact.signatures:
                p = BNode()
                o = self.namespaces['ccd'][signature[1]['label']]
                rdf_g.add((s, p, o))
            # Add labels
            for label in artefact.labels:
                p = RDFS.label
                o = Literal(label[1]['label'])
                rdf_g.add((s, p, o))

        # Write non-binary metadata
        with open(file, 'w') as f:
            f.write('# @Author(s): ' + self.author + '\n')

        # Write binary-serialized data
        with open(file, 'ab') as f:
            rdf_g.serialize(destination=f, format='n3')

        # Replace [ ] representation of blank nodes by 'a' representation (A bit hacky, better option available?)
        with open(file, "r") as f:
            old = f.read()

        new = old.replace('[ ]', 'a')

        with open(file, "w") as f:
            f.write(new)


# Initialize workflow object
wf = Workflow()

# Extract actions from nodes and edges in a DAG
networkx_dag = nx.read_graphml('wfMnT_neighborhoods.graphml')
wf.update_metadata_from_networkx_dag(networkx_dag)
wf.import_data_from_networkx_dag(networkx_dag)

wf.export_to_RDF('wfMnT_neighborhoods.ttl')








