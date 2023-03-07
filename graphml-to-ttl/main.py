import networkx as nx
from rdflib import Graph, Namespace, RDF, RDFS, URIRef, BNode
from rdflib.term import Literal
import os

# Libraries for parsing CCT expressions
from cct import cct
import transforge as tf


class Action:
    def __init__(self, action_node=None, inputs=None, outputs=None, comments=None, expressions=None, labels=None,
                 compositions=None):
        self.node = action_node
        self.inputs = inputs
        self.outputs = outputs
        self.comments = comments
        self.expressions = expressions
        self.labels = labels
        self.compositions = compositions

    def __str__(self):
        return f""" 
{'Action:' : >13} {self.node}
{'Inputs:' : >13} {self.inputs}
{'Outputs:' : >13} {self.outputs}
{'Comments:' : >13} {self.comments}
{'Expressions:' : >13} {self.expressions}
{'Labels:' : >13} {self.labels}
{'Compositions:' : >13} {self.compositions}"""

    # Method for testing syntax of CCT expressions (NOTE: testing is done when importing expression to expressions)
    def test_cct_expression(self, complex_string):
        return cct.parse(complex_string, *(tf.Source() for _ in range(10)))


class Artefact:
    def __init__(self, artefact_node=None, inputs=None, outputs=None, comments=None, signatures=None, labels=None):
        self.node = artefact_node
        self.inputs = inputs
        self.outputs = outputs
        self.comments = comments
        self.signatures = signatures
        self.labels = labels

    def __str__(self):
        return f"""
{'Artefact:' : >11} {self.node}  
{'Inputs:' : >11} {self.inputs}
{'Outputs:' : >11} {self.outputs}
{'Comments:' : >11} {self.comments}
{'Signatures:' : >11} {self.signatures}"""


class Workflow:
    def __init__(self, name='', author='Unknown', comment='', subject='', abstract='.'):
        self.name = name
        self.author = author
        self.actions = set()
        self.artefacts = set()
        # Make static attribute / global? Potentially, wf's need different namespaces due to different data sources
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
        }
        self.comment = comment
        self.subject = subject
        self.abstract = abstract
        self.sources = set()

    def import_data_from_networkx_dag(self, dag):

        # # # Add metadata using edge labels # # #
        self.sources = set()  # Empty existing sources

        for edge in dag.edges(data=True):
            # Get author, question, subject, abstract metadata using edge labels
            if 'label' in edge[2]:
                edge_label = edge[2]['label']
                origin_label = dag.nodes[edge[0]]['label']
                if edge_label == 'Author':
                    self.author = origin_label
                elif edge_label == 'Question':
                    self.comment = origin_label
                elif edge_label == 'Subject':
                    self.subject = origin_label
                elif edge_label == 'Abstract':
                    self.abstract = origin_label

            # Get source labels by whether they are starting nodes
            if dag.nodes[edge[0]]['shape_type'] == 'parallelogram' and all(edge[0] != edge2[1] for edge2 in dag.edges):
                self.sources.add(dag.nodes[edge[0]]['label'])

        # # # Add data using node shapes and edges between node shapes # # #
        for node in dag.nodes(data=True):
            if node[1]['shape_type'] == 'trapezoid':
                print(node)
                exit()

            # Create artefacts from nodes
            if node[1]['shape_type'] in ['parallelogram']:
                inputs, outputs, comments, signatures, labels = [], [], [], [], []
                for edge in dag.edges:
                    origin_node = dag.nodes[edge[0]]
                    destination_node = dag.nodes[edge[1]]
                    if node[0] == edge[1] and origin_node['shape_type'] == 'roundrectangle':
                        inputs.append((edge[0], origin_node))
                    elif node[0] == edge[0] and destination_node['shape_type'] == 'roundrectangle':
                        outputs.append((edge[1], destination_node))
                    elif node[0] == edge[1] and origin_node['shape_type'] == 'fatarrow':
                        comments.append((edge[0], origin_node))
                    elif node[0] == edge[1] and origin_node['shape_type'] == 'octagon':
                        signatures.append((edge[0], origin_node))
                    elif node[0] == edge[1] and origin_node['shape_type'] == 'hexagon':
                        labels.append((edge[0], origin_node))
                self.artefacts.add(Artefact(node, inputs, outputs, comments, signatures, labels))

            # Create actions from nodes
            if node[1]['shape_type'] == 'roundrectangle':
                inputs, outputs, comments, expressions, labels, compositions = [], [], [], [], [], []
                for edge in dag.edges:
                    origin_node = dag.nodes[edge[0]]
                    destination_node = dag.nodes[edge[1]]
                    if node[0] == edge[1] and origin_node['shape_type'] == 'parallelogram':
                        inputs.append((edge[0], origin_node))
                    elif node[0] == edge[0] and destination_node['shape_type'] == 'parallelogram':
                        outputs.append((edge[1], destination_node))
                    elif node[0] == edge[1] and origin_node['shape_type'] == 'fatarrow':
                        comments.append((edge[0], origin_node))
                    elif node[0] == edge[1] and origin_node['shape_type'] == 'octagon':
                        # N:
                        # I'm assuming that an action can have at most one expression, right? I'd suggest that
                        # such things be reflected by not putting it in a list (and explicitly assert your assumptions,
                        # so that things crash if it's a wrong assumption).
                        # E:
                        # It's true that we only need one expression per action. However, there are some reasons to keep
                        # this functionality. Maybe we come up with a method for conjunction/disjunction of expressions,
                        # or we want to consider inter-annotator agreement. That's why I think it is better to have this
                        # assertion at a point further down the pipeline.

                        expressions.append((edge[0], origin_node))
                    elif node[0] == edge[1] and origin_node['shape_type'] == 'hexagon':
                        labels.append((edge[0], origin_node))
                    elif node[0] == edge[1] and origin_node['shape_type'] == 'star5':
                        compositions.append((edge[0], origin_node))
                self.actions.add(Action(node, inputs, outputs, comments, expressions, labels, compositions))

    def process_compositions(self):

        # Gather all composite actions to be composed from existing actions
        compositions = list()

        for action in self.actions.copy():
            for composition in action.compositions:
                compositions.append((composition, action))

    def export_to_RDF(self, file):
        rdf_g = Graph()

        # Blank node namespace
        # self.namespaces.update({'_': Namespace('#')})

        # Add namespaces to file
        for prefix, namespace in self.namespaces.items():
            rdf_g.bind(prefix, namespace)

        # Add workflow triples
        origin = self.namespaces['repo'][self.name] # subject remains constant over triples

        # Workflow name
        rdf_g.add((origin,
                   BNode(),
                   self.namespaces['wf']['Workflow']))

        # Question
        rdf_g.add((origin,
                   RDFS.comment,
                   Literal(self.comment)))

        # Subject
        rdf_g.add((origin,
                   self.namespaces['dct']['subject'],
                   Literal(self.subject)))

        # Abstract
        rdf_g.add((origin,
                   self.namespaces['dbo']['abstract'],
                   Literal(self.abstract)))

        # Sources
        for source in self.sources:
            rdf_g.add((origin,
                       self.namespaces['wf']['source'],
                       self.namespaces['data'][self.name + source]))

        # Add actions
        for action in self.actions:
            rdf_g.add((origin,
                       self.namespaces['wf']['edge'],
                       self.namespaces['data'][self.name + str(action.node[0])]))

        # Add action-specific triples to rdf_graph
        for action in self.actions:

            # Add tool node
            origin = self.namespaces['data'][self.name + str(action.node[0])]
            rdf_g.add((origin,
                       self.namespaces['wf']['applicationOf'],
                       self.namespaces['tools'][action.node[1]['label']]))

            # Add input nodes
            for count, input in enumerate(action.inputs):
                rdf_g.add((origin,
                           self.namespaces['wf']['input'] + str(count),
                           self.namespaces['data'][self.name + str(input[1]['label'])]))

            # Add comments
            for comment in action.comments:
                rdf_g.add((origin,
                           RDFS.comment,
                           Literal(comment[1]['label'])))

            # Add output nodes
            for output in action.outputs:
                rdf_g.add((origin,
                           self.namespaces['wf']['output'],
                           self.namespaces['data'][self.name + str(output[1]['label'])]))

            # Add expressions
            for expression in action.expressions:
                rdf_g.add((origin,
                           self.namespaces['cct']['expression'],
                           Literal(expression[1]['label'])))

            # Add labels
            for label in action.labels:
                rdf_g.add((origin,
                           RDFS.label,
                           Literal(label[1]['label'])))

        # Add artefacts
        for artefact in self.artefacts:
            origin = self.namespaces['data'][self.name + artefact.node[1]['label']]
            # Add artefact comments
            for comment in artefact.comments:
                rdf_g.add((origin,
                           RDFS.comment,
                           Literal(comment[1]['label'])))
            # Add artefact comments
            for signature in artefact.signatures:
                rdf_g.add((origin,
                           BNode(),
                           self.namespaces['ccd'][signature[1]['label']]))
            # Add labels
            for label in artefact.labels:
                rdf_g.add((origin,
                           RDFS.label,
                           Literal(label[1]['label'])))

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




def process_all():
    # Export all .graphml files to .ttl files
    for file in os.listdir('../data_source/graphml/'):
        filename_parts = os.path.splitext(file)

        # Check if the file is a .graphml file
        if os.path.splitext(file)[1] == ".graphml":

            # Initialize workflow object
            wf = Workflow()

            # Import file into networkx
            networkx_dag = nx.read_graphml('../data_source/graphml/' + file)

            # Convert metadata to rdflib.graph workflow metadata
            wf.update_metadata_from_networkx_dag(networkx_dag)


            # Convert data to rdflib.graph workflow action/artefact data
            wf.import_data_from_networkx_dag(networkx_dag)


            # Export to RDF .ttl format
            wf.export_to_RDF('../data_source/ttl/' + filename_parts[0] + '.ttl')


def main():
    wf = Workflow()
    networkx_dag = nx.read_graphml('../data_source/graphml/wfaccess.graphml')
    wf.import_data_from_networkx_dag(networkx_dag)
    wf.process_compositions()
    wf.export_to_RDF('../data_source/graphml/wfaccess.ttl')

    for action in wf.actions:
        print(action)

    # Export all .graphml files in the semantics subfolder to .ttl files
    # indir = '../data_source/graphml/wfsemantics/'
    # outdir = '../data_source/ttl/wfsemantics/'
    # for file in os.listdir(indir):
    #    filename_parts = os.path.splitext(file)


main()
