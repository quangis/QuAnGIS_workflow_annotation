
# Libraries for parsing CCT expressions
from cct import cct
import transforge as tf


# A node together with all its directly-related edges
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

    @classmethod
    def get_cache(cls):
        return cls._instances

    @classmethod
    def clear_cache(cls):
        cls._instances.clear()


# Tests whether the passed string is a valid CCT expression. Used for expression assignment
def test_cct_expression(complex_string):
    return cct.parse(complex_string, *(tf.Source() for _ in range(10)))


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
        self.components = dict()  # nodes to store actions that compose this action.
        self.compositions = dict()  # nodes to store actions that are composed by this action.
        self.abstracts = dict()  # Converts to dbo:abstract
        self.authors = dict()  # Converts to notation in RDF file

        for edge in self.edges:
            # Cases where the hub is the node of departure (hub is x in (x, y), other is y)
            if node == edge[0]:
                other = edge[1]
                other_shape = graph.nodes[other]['shape_type']

                if other_shape == 'parallelogram':  # outputs
                    self.outputs[len(self.inputs)+1] = other
                elif other_shape == 'roundrectangle':  # components
                    self.components[len(self.components)+1] = other

            # Cases where the hub is the node of arrival (hub is y in (x, y), other is x)
            elif node == edge[1]:
                other = edge[0]
                other_shape = graph.nodes[other]['shape_type']

                # Check for custom edge labels. If so, add as dictionary keys
                if 'label' in edge[2]:
                    if other_shape == 'parallelogram':  # inputs
                        self.inputs[edge[2]['label']] = other
                    elif other_shape == 'fatarrow':  # comments
                        self.comments[edge[2]['label']] = other
                    elif other_shape == 'octagon':  # comments
                        try:
                            graph.nodes[other]['label'] = graph.nodes[other]['label']
                            test_cct_expression(graph.nodes[other]['label'])
                        except:
                            print('node ' + str(other) + ' has invalid cct: ' + graph.nodes[other]['label'])
                            graph.nodes[other]['label'] += '#INVALID_EXPRESSION#'
                        self.expressions[edge[2]['label']] = other
                    elif other_shape == 'hexagon':  # comments
                        self.labels[edge[2]['label']] = other
                    elif other_shape == 'roundrectangle':  # comments
                        self.compositions[edge[2]['label']] = other
                    elif other_shape == 'triangle2':
                        self.abstracts[edge[2]['label']] = other
                    elif other_shape == 'star8':
                        self.authors[edge[2]['label']] = other

                # If no custom edge labels, generate dictionary keys
                else:
                    if other_shape == 'parallelogram':  # inputs
                        self.inputs[len(self.inputs)] = other
                    elif other_shape == 'fatarrow':  # comments
                        self.comments[len(self.comments)] = other
                    elif other_shape == 'octagon':  # expressions
                        try:
                            graph.nodes[other]['label'] = graph.nodes[other]['label']
                            test_cct_expression(graph.nodes[other]['label'])
                        except:
                            print('node ' + str(other) + ' has invalid cct: ' + graph.nodes[other]['label'])
                            graph.nodes[other]['label'] += '#INVALID_EXPRESSION#'
                        self.expressions[len(self.expressions)] = other
                    elif other_shape == 'hexagon':  # labels
                        self.labels[len(self.labels)] = other
                    elif other_shape == 'roundrectangle':  # compositions
                        self.compositions[len(self.compositions)] = other
                    elif other_shape == 'triangle2':
                        self.abstracts[len(self.abstracts)] = other
                    elif other_shape == 'star8':
                        self.authors[len(self.authors)] = other

        # Get inputs and outputs if they are not explicitly defined (E.g., in the case of the context action)
        if not self.inputs or not self.outputs:
            # Iterate over own components, collecting inputs and outputs
            input_candidates = []
            output_candidates = []

            for value in self.components.values():
                component = Action(value, self.graph)  # Note: Actions are cached; no duplicates are generated
                input_candidates += [x for x in component.inputs.values()]
                output_candidates += [x for x in component.outputs.values()]

            inputs, outputs = derive_outer_nodes(input_candidates, output_candidates)
            for input in inputs:
                self.inputs[len(self.inputs)] = input
            for output in outputs:
                self.outputs[len(self.outputs)] = output

    def __str__(self):
        node = self.graph.nodes[self.node]['label']
        inputs = [(self.inputs[x], self.graph.nodes[self.inputs[x]]['label']) for x in self.inputs]
        outputs = [(self.outputs[x], self.graph.nodes[self.outputs[x]]['label']) for x in self.outputs]
        comments = [(self.comments[x], self.graph.nodes[self.comments[x]]['label']) for x in self.comments]
        labels = [(self.labels[x], self.graph.nodes[self.labels[x]]['label']) for x in self.labels]
        expressions = [(self.expressions[x], self.graph.nodes[self.expressions[x]]['label']) for x in self.expressions]
        components = [(self.components[x], self.graph.nodes[self.components[x]]['label']) for x in self.components]
        compositions = [(self.compositions[x], self.graph.nodes[self.compositions[x]]['label']) for x in
                        self.compositions]
        abstracts = [(self.abstracts[x], self.graph.nodes[self.abstracts[x]]['label']) for x in self.abstracts]
        authors = [(self.authors[x], self.graph.nodes[self.authors[x]]['label']) for x in self.authors]
        return f"""
{'Action_ID:':>13} {self.node, node}
{'Inputs:':>13} {inputs}
{'Outputs:':>13} {outputs}
{'Comments:':>13} {comments}
{'Labels:':>13} {labels}
{'Expressions:':>13} {expressions}
{'Components:':>13} {components}
{'Compositions:':>13} {compositions}
{'Abstracts:':>13} {abstracts}
{'Authors:':>13} {authors}
"""


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
            # Cases where the hub is the node of departure (hub is x in (x, y), other is y)
            if node == edge[0]:
                pass

            # Cases where the hub is the node of arrival (hub is y in (x, y), other is x)
            elif node == edge[1]:
                other = edge[0]
                other_shape = graph.nodes[other]['shape_type']
                if other_shape == 'fatarrow':  # comments
                    self.comments[len(self.comments)] = other
                elif other_shape == 'octagon':  # expressions
                    self.signatures[len(self.signatures)] = other
                elif other_shape == 'hexagon':  # labels
                    self.labels[len(self.labels)] = other

    def __str__(self):
        node = self.graph.nodes[self.node]['label']
        comments = [(self.comments[x], self.graph.nodes[self.comments[x]]['label']) for x in self.comments]
        labels = [(self.labels[x], self.graph.nodes[self.labels[x]]['label']) for x in self.labels]
        signatures = [(self.signatures[x], self.graph.nodes[self.signatures[x]]['label']) for x in self.signatures]

        return f"""
{'Artefact_ID:':>13} {self.node, node}
{'Comments:':>13} {comments}
{'Labels:':>13} {labels}
{'Expressions:':>13} {signatures}
"""


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




