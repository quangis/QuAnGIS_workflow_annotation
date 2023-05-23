# Libraries for parsing CCT expressions
import networkx as nx
import rdflib as rdf

import transforge as tf
from cct import cct

# # # Data declaration  # # #
namespaces = {
    'rdf': rdf.Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#'),
    'rdfs': rdf.Namespace('http://www.w3.org/2000/01/rdf-schema#'),
    'xsd': rdf.Namespace('http://www.w3.org/2001/XMLSchema#'),
    'xml': rdf.Namespace('http://www.w3.org/XML/1998/namespace'),
    'dbo': rdf.Namespace('https://dbpedia.org/ontology/'),
    'dct': rdf.Namespace('http://purl.org/dc/terms/'),
    'wf': rdf.Namespace('http://geographicknowledge.de/vocab/Workflow.rdf#'),
    'tools': rdf.Namespace('https://quangis.github.io/tool/arcgis#'),
    'repo': rdf.Namespace('https://example.com/#'),
    'data': rdf.Namespace('https://github.com/quangis/cct/blob/master/tools/data.ttl#'),
    'ccd': rdf.Namespace('http://geographicknowledge.de/vocab/CoreConceptData.rdf#'),
    'cct': rdf.Namespace('https://github.com/quangis/cct#')
}
cct_test_cache = {}  # Stores nodes that already had their expressions tested
ccd_test_cache = {}  # Stores nodes that already had their signatures tested


# # # Auxiliary functions # # #
def check_graph(g):
    def check_artefacts(g):
        artefact_nodes = [node for node in g.nodes if g.nodes[node]['shape_type'] == 'parallelogram']
        for idx1, a1 in enumerate(artefact_nodes):
            for idx2, a2 in enumerate(artefact_nodes):
                if idx1 != idx2 and g.nodes[a1]['label'] == g.nodes[a2]['label']:
                    if g.nodes[a2]['label'][-1].isdigit():
                        g.nodes[a2]['label'] = g.nodes[a2]['label'][:-1] + str(int(g.nodes[a2]['label'][-1]) + 1)
                    else:
                        g.nodes[a2]['label'] += '2'
                    check_artefacts(g)
    check_artefacts(g)


# Clears Hub._instances, cct_test_cache, ccd_test_cache
def clear_all_caches():
    Hub.clear_cache()
    ccd_test_cache.clear()
    cct_test_cache.clear()


# Puts a node in a variable dictionary. If a label is specified, the key will be that label
def store_item(other, dictionary, edge_label=None, increment_key=False):
    # Check if the other node fits the classification condition
    if edge_label:
        dictionary[edge_label] = other
    else:
        if increment_key:
            dictionary[len(dictionary)+1] = other  # Used for inputs, so that the first input is input1
        else:
            dictionary[len(dictionary)] = other


# Tests whether the passed string is a valid CCT expression. Used for expression assignment
def test_cct_expression(complex_string):
    return cct.parse(complex_string, *(tf.Source() for _ in range(10)))


# Tests whether a node in a graph has a valid CCT expression. If not, add notifier to the node label
def test_cct_expression_node(node, graph):
    if not node in cct_test_cache.values():
        test_cct_expression(graph.nodes[node]['label'])
        try:
            test_cct_expression(graph.nodes[node]['label'])
        except:
            print('node ' + str(node) + ' has invalid cct: ' + graph.nodes[node]['label'])
            graph.nodes[node]['label'] += '#INVALID_EXPRESSION#'
        finally:
            cct_test_cache[len(cct_test_cache)] = node


# Tests whether the signature is available in the CCD-ontology
def is_valid_ccd_signature(ccd_string):
    ccd = rdf.Graph()
    ccd.parse('http://www.geographicknowledge.de/vocab/CoreConceptData.ttl')

    for subject in ccd.subjects():
        if isinstance(subject, rdf.URIRef):
            if '#' in str(subject):
                if ccd_string == str(subject).split('#')[1]:
                    return True
    return False


# Tests whether a node in a graph has a valid CCD signature. If not, add notifier to the node label
def test_ccd_signature_node(node, graph):
    if not node in ccd_test_cache.values():
        if not is_valid_ccd_signature(graph.nodes[node]['label']):
            print('node ' + str(node) + ' has invalid ccd: ' + graph.nodes[node]['label'])
            graph.nodes[node]['label'] += '#INVALID_SIGNATURE#'
        ccd_test_cache[len(ccd_test_cache)] = node


# Derives x as input and z as output from e.g., (x,y), (y,z).
def derive_outer_nodes(input_candidates, output_candidates):
    inputs = []
    # Only keep inputs that are not outputs
    for candidate in input_candidates:
        if not any(output == candidate for output in output_candidates):
            inputs.append(candidate)

    outputs = []
    # Only keep outputs that are not inputs
    for candidate in output_candidates:
        if not any(input == candidate for input in input_candidates):
            outputs.append(candidate)

    return inputs, outputs


# Collects all nodes reachable through a depth-first search. Propagates backwards; Invoke with output node
# If a set of limits is passed, the search is up to and including those limits
def dfs(edges, node, reverse=False, seen=None, limit=set()):
    if seen is None:
        seen = set()
    seen.add(node)

    if node not in limit:
        if reverse:
            for edge in {edge for edge in edges if node == edge[1]}:
                if edge[0] not in seen:
                    seen = seen.union(dfs(edges, edge[0], reverse, seen, limit))
        else:
            for edge in {edge for edge in edges if node == edge[0]}:
                if edge[1] not in seen:
                    seen = seen.union(dfs(edges, edge[1], reverse, seen, limit))
    return seen


# Adds the entire workflow as another action to the graph
def add_context_edges(graph):
    input_candidates = []
    output_candidates = []
    metadata = []

    # If a context node is provided, add context edges
    for node in graph.nodes(data=True):
        if node[1]['shape_type'] == 'trapezoid':
            node[1]['shape_type'] = 'roundrectangle'
            for edge in graph.edges(data=True):
                l, r = edge[0], edge[1]
                l_shape = graph.nodes[l]['shape_type']
                r_shape = graph.nodes[r]['shape_type']
                if l_shape == 'parallelogram' and r_shape == 'roundrectangle':
                    input_candidates.append(l)
                elif l_shape == 'roundrectangle' and r_shape == 'parallelogram':
                    output_candidates.append(r)
            inputs, outputs = derive_outer_nodes(input_candidates, output_candidates)
            for incoming in [*inputs, *metadata]:
                graph.add_edge(incoming, node[0])
            for output in outputs:
                graph.add_edge(node[0], output)
            return


# # # Classes # # #
# A node in a graph together with all its directly-related edges
class Hub:
    _instances = dict()

    def __init__(self, node, graph):
        self.node = node
        self.edges = list()
        self.graph = graph

        # Select edges that are directly-related to the node and use them to form node tuples
        for edge in graph.edges(data=True):
            if node in edge:
                self.edges.append(edge)

    def __new__(cls, node, graph):
        if node not in cls._instances:
            instance = super().__new__(cls)
            instance.value = node
            cls._instances[node] = instance
        else:
            instance = cls._instances[node]
        return instance

    def __eq__(self, other):
        if isinstance(other, Hub):
            return self.node == other.node and self.graph == other.graph
        return False

    # Used in subclasses with dicts as attributes;
    def list_nodes_in_dict(self, dictionary):
        return [(dictionary[x], self.graph.nodes[dictionary[x]]['label']) for x in dictionary]

    @classmethod
    def get_cache(cls):
        return cls._instances

    @classmethod
    def clear_cache(cls):
        cls._instances.clear()


# A node in a graph representing some sort of action together with its inputs, outputs, and metadata (id by shape)
class Action(Hub):
    def __new__(cls, node, graph):
        if node not in cls._instances:
            instance = super().__new__(cls, node, graph)
            instance.value = node
            cls._instances[node] = instance
        else:
            instance = cls._instances[node]
        return instance

    def __init__(self, node, graph):
        super().__init__(node, graph)

        # Test if node represents an action
        if not graph.nodes[node]['shape_type'] == 'roundrectangle':
            raise ValueError('Tried to initialize a non-action node as action')

        self.inputs = dict()  # Incoming artefact nodes. Converts to wf:input<input no.> in RDF
        self.outputs = dict()  # Outgoing artefact nodes. Converts to wf:output in RDF
        self.comments = dict()  # Converts to rdfs:comment in RDF
        self.labels = dict()  # Converts to rdfs:label in RDF
        self.expressions = dict()  # nodes to store cct-algebra expressions. Converts to cct:expression and dct:subject
        self.abstracts = dict()  # Converts to dbo:abstract
        self.authors = dict()  # Converts to notation in RDF file
        self.schemas = dict()  # lists of actions that run parallel with this action. Can be used to write wf .ttl files

        for edge in self.edges:

            # Define an edge label if possible
            edge_label = None
            if 'label' in edge[2]:
                edge_label = edge[2]['label']

            # Cases where the hub is the node of departure (hub is x in (x, y), other is y)
            if self.node == edge[0]:
                other = edge[1]
                other_shape = self.graph.nodes[other]['shape_type']
                if other_shape == 'parallelogram':  # outputs
                    store_item(other, self.outputs, edge_label)

            # Cases where the hub is the node of arrival (hub is y in (x, y), other is x)
            elif self.node == edge[1]:
                other = edge[0]
                other_shape = self.graph.nodes[other]['shape_type']
                if other_shape == 'parallelogram':
                    if edge_label:
                        store_item(other, self.inputs, edge_label + '_manual')
                    else:
                        store_item(other, self.inputs, edge_label, increment_key=True)
                elif other_shape == 'fatarrow':
                    store_item(other, self.comments, edge_label)
                elif other_shape == 'octagon':
                    test_cct_expression_node(other, self.graph)
                    store_item(other, self.expressions, edge_label)
                elif other_shape == 'hexagon':
                    store_item(other, self.labels, edge_label)
                elif other_shape == 'triangle2':
                    store_item(other, self.abstracts, edge_label)
                elif other_shape == 'star8':
                    store_item(other, self.authors, edge_label)

        # Define schemas
        for edge in graph.edges:

            # Get edges that run into the output. If the departure is not the current action, continue over branch
            if edge[1] in self.outputs.values() and edge[0] != self.node:

                # Get all nodes down the branch
                parallels = dfs(graph.edges, edge[0], reverse=True, limit=set(self.inputs.values()))
                parallels = parallels.union(self.outputs.values())

                # Filter out actions and input/outputs
                shape_types = ['parallelogram', 'roundrectangle']
                action_nodes = [node for node in parallels if graph.nodes[node]['shape_type'] == shape_types[1]]
                artefact_nodes = [node for node in parallels if graph.nodes[node]['shape_type'] == shape_types[0]]
                nodes = action_nodes + artefact_nodes

                # Determine which nodes are outer data nodes
                input_candidates = set()
                output_candidates = {edge[1]}
                for sub_edge in graph.subgraph(nodes).edges:
                    if sub_edge[0] in artefact_nodes and sub_edge[1] in action_nodes:
                        input_candidates.add(sub_edge[0])
                    elif sub_edge[0] in action_nodes and sub_edge[1] in artefact_nodes:
                        output_candidates.add(sub_edge[1])
                inputs, outputs = derive_outer_nodes(input_candidates, output_candidates)

                # If outer inputs and outer outputs are equal to action inputs and action output
                if (set(inputs), set(outputs)) == (set(self.inputs.values()), set(self.outputs.values())):
                    # Define schema over the branch
                    store_item(Schema(self, action_nodes, artefact_nodes, graph), self.schemas)

    def __str__(self):
        node = self.graph.nodes[self.node]['label']
        return f"""
{'Action_ID:':>13} {self.node, node}
{'Inputs:':>13} {self.list_nodes_in_dict(self.inputs)}
{'Outputs:':>13} {self.list_nodes_in_dict(self.outputs)}
{'Comments:':>13} {self.list_nodes_in_dict(self.comments)}
{'Labels:':>13} {self.list_nodes_in_dict(self.labels)}
{'Expressions:':>13} {self.list_nodes_in_dict(self.expressions)}
{'Abstracts:':>13} {self.list_nodes_in_dict(self.abstracts)}
{'Authors:':>13} {self.list_nodes_in_dict(self.authors)}
"""

    # Add information to existing rdf graph
    def add_to_rdf(self, rdf_graph, context=None):
        self_label = self.graph.nodes[self.node]['label']

        if context is not None:
            context_label = context.graph.nodes[context.node]['label']
            #context_node = namespaces['tools'][context_label]
            context_node = rdf.term.BNode(context_label)

            # Add triple between context and action
            rdf_graph.add((context_node,
                           namespaces['wf']['edge'],
                           rdf.term.BNode(self.node))) #namespaces['data'][self.node]))

        # Add triple between action and its tool
        if self.schemas:  # Check if an action implements a supertool (May need to be a more sophisticated check)
            rdf_graph.add((rdf.term.BNode(self.node),  # namespaces['data'][self.node],
                           namespaces['wf']['applicationOf'],
                           rdf.term.BNode(self_label)))
            # Add an rdfs:label
            rdf_graph.add((rdf.term.BNode(self_label),  # namespaces['data'][self.node],
                           namespaces['rdfs']['label'],
                           rdf.Literal(self_label)))
        else:
            rdf_graph.add((rdf.term.BNode(self.node), #namespaces['data'][self.node],
                           namespaces['wf']['applicationOf'],
                           namespaces['tools'][self_label]))

        # Add inputs
        for input in self.inputs.items():
            predicate = namespaces['wf']['inputx']
            if isinstance(input[0], str):
                if '_manual' in input[0]:
                    predicate = namespaces['wf']['input' + input[0].replace('_manual', '')]

            input_label = self.graph.nodes[input[1]]['label']
            rdf_graph.add((rdf.term.BNode(self.node), #namespaces['data'][self.node],
                           predicate,
                           rdf.term.BNode(input_label))) #namespaces['data'][input_label]))

        # Add outputs
        for output in self.outputs.items():
            output_label = self.graph.nodes[output[1]]['label']
            rdf_graph.add((rdf.term.BNode(self.node), #namespaces['data'][self.node],
                           namespaces['wf']['output'],
                           rdf.term.BNode(output_label)))#namespaces['data'][output_label]))

        # Add expressions
        for expression in self.expressions.items():
            expression_label = self.graph.nodes[expression[1]]['label']
            rdf_graph.add((rdf.term.BNode(self.node), #namespaces['data'][self.node],
                           namespaces['cct']['expression'],
                           rdf.Literal(expression_label)))

        # Add comments
        for comment in self.comments.items():
            comment_label = self.graph.nodes[comment[1]]['label']
            rdf_graph.add((rdf.term.BNode(self.node), #namespaces['data'][self.node],
                           rdf.RDFS.comment,
                           rdf.Literal(comment_label)))

        # Add labels
        for label in self.labels.items():
            label_label = self.graph.nodes[label[1]]['label']
            rdf_graph.add((rdf.term.BNode(self.node), #namespaces['data'][self.node],
                           rdf.RDFS.label,
                           rdf.Literal(label_label)))

        # Add schemas
        for schema in self.schemas.values():
            schema.add_to_rdf(rdf_graph)

    def to_rdf_graph(self):
        rdf_graph = rdf.Graph()
        self.add_to_rdf(rdf_graph)
        return rdf_graph

    def to_ttl(self, file):
        rdf_graph = self.to_rdf_graph()

        for prefix, namespace in namespaces.items():
            rdf_graph.bind(prefix, namespace)

        # Write non-binary metadata
        with open(file, 'w') as f:
            authors = '# @Author(s): '
            for author in self.authors.items():
                authors += self.graph.nodes[author[1]]['label'] + ', '
            f.write(authors + '\n')

        # Write binary-serialized data
        with open(file, 'ab') as f:
            rdf_graph.serialize(destination=f, format='n3')


# A node in a graph representing some sort of static artefact or dataset, together with its metadata (id by shape)
class Artefact(Hub):
    def __init__(self, node, graph):
        super().__init__(node, graph)

        # Test if node represents an action
        if not graph.nodes[node]['shape_type'] == 'parallelogram':
            raise ValueError('Tried to initialize a non-action node as action')

        self.comments = dict()  # Nodes to store additional comments
        self.labels = dict()  # Nodes to store concise labels
        self.signatures = dict()  # nodes to store algebra expressions

        for edge in self.edges:

            # Define an edge_label if possible
            edge_label = None
            if 'label' in edge[2]:
                edge_label = edge[2]['label']

            # Cases where the hub is the node of departure (hub is x in (x, y), other is y)
            if node == edge[0]:
                pass  # no cases currently

            # Cases where the hub is the node of arrival (hub is y in (x, y), other is x)
            elif node == edge[1]:
                other = edge[0]
                other_shape = graph.nodes[other]['shape_type']
                if other_shape == 'fatarrow':
                    store_item(other, self.comments, edge_label)
                elif other_shape == 'octagon':
                    test_ccd_signature_node(other, self.graph)
                    store_item(other, self.signatures, edge_label)
                elif other_shape == 'hexagon':
                    store_item(other, self.labels, edge_label)

    def __str__(self):
        node = self.graph.nodes[self.node]['label']

        return f"""
{'Artefact_ID:':>13} {self.node, node}
{'Comments:':>13} {self.list_nodes_in_dict(self.comments)}
{'Labels:':>13} {self.list_nodes_in_dict(self.labels)}
{'Signatures:':>13} {self.list_nodes_in_dict(self.signatures)}
"""

    def add_to_rdf(self, rdf_graph):
        artefact_label = self.graph.nodes[self.node]['label']

        # Add comments
        for comment in self.comments.items():
            comment_label = self.graph.nodes[comment[1]]['label']
            rdf_graph.add((rdf.term.BNode(artefact_label), #namespaces['data'][artefact_label],
                           rdf.RDFS.comment,
                           rdf.Literal(comment_label)))

        # Add labels
        for label in self.labels.items():
            label_label = self.graph.nodes[label[1]]['label']
            rdf_graph.add((rdf.term.BNode(artefact_label), #namespaces['data'][artefact_label],
                           rdf.RDFS.label,
                           rdf.Literal(label_label)))

        # Add signatures
        for signature in self.signatures.items():
            signature_label = self.graph.nodes[signature[1]]['label']
            rdf_graph.add((rdf.term.BNode(artefact_label), #namespaces['data'][artefact_label],
                           rdf.RDF.type,
                           namespaces['ccd'][signature_label]))


# A structure over an action, its graph, and a sequence of actions that substitute the action in the graph
class Schema:
    def __init__(self, context, actions, artefacts, graph):

        # Get edges, inputs and outputs
        self.context = context
        self.actions = actions
        self.artefacts = artefacts
        self.graph = graph

        edges = set()
        input_candidates = set()
        output_candidates = set()
        for action in actions:
            action = Action(action, graph)
            for input in action.inputs.values():
                input_candidates.add(input)
                for output in action.outputs.values():
                    output_candidates.add(output)
                    edges.add((input, output))

        self.inputs, outputs = derive_outer_nodes(input_candidates, output_candidates)

        # Check whether there is only one output
        if not len(outputs) == 1:
            raise ValueError('More than one output in schema')

        self.output = outputs[0]

        # Check whether the edges form a connected graph using depth-first search
        if not dfs(edges, self.output, reverse=True) == input_candidates.union(output_candidates):
            raise ValueError('Schema is disconnected')

    def add_to_rdf(self, rdf_graph):
        action_label = self.context.graph.nodes[self.context.node]['label']
        #action_rdf_node = namespaces['tools'][action_label]
        action_rdf_node = rdf.term.BNode(action_label)

        # Workflow name
        rdf_graph.add((action_rdf_node,
                       rdf.RDF.type,
                       namespaces['wf']['Workflow']))

        # Context comments
        for comment in self.context.comments.items():
            rdf_graph.add((action_rdf_node,
                           rdf.RDFS.comment,
                           rdf.Literal(self.graph.nodes[comment[1]]['label'])))
        # Context subjects
        for expression in self.context.expressions.items():
            rdf_graph.add((action_rdf_node,
                           namespaces['dct']['subject'],
                           rdf.Literal(self.graph.nodes[expression[1]]['label'])))
        # Context abstracts
        for abstract in self.context.abstracts.items():
            rdf_graph.add((action_rdf_node,
                           namespaces['dbo']['abstract'],
                           rdf.Literal(self.graph.nodes[abstract[1]]['label'])))
        # Context Sources
        for source in self.context.inputs.items():
            rdf_graph.add((action_rdf_node,
                           namespaces['wf']['source'],
                           rdf.term.BNode(self.graph.nodes[source[1]]['label']))) #namespaces['data'][self.graph.nodes[source[1]]['label']]))

        # Add action data
        for sub_action in self.actions:
            Action(sub_action, self.graph).add_to_rdf(rdf_graph, self.context)

        # add artefact data
        for sub_artefact in self.artefacts:
            Artefact(sub_artefact, self.graph).add_to_rdf(rdf_graph)
