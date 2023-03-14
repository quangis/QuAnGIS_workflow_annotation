import networkx as nx
import rdflib as rdf
import os
from hubs import *
from rdflib import *

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
        statement = "Action: " + str(self.node) + "\n"
        statement += "Inputs: " + str(self.inputs) + "\n"
        statement += "Outputs: " + str(self.outputs) + "\n"
        statement += "Comments: " + str(self.comments) + "\n"
        statement += "Expressions: " + str(self.expressions) + "\n"
        statement += "Labels: " + str(self.labels) + "\n"
        statement += "Compositions: " + str(self.compositions) + "\n"
        return statement

    # Method for testing syntax of CCT expressions
    def ccttest(self,complex_string):
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
        self.compositions = set()
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
                compositions = list()
                for edge in dag.edges(data=True):
                    if 'label' in edge[2]:
                        inputnr = edge[2]['label']
                    else:
                        inputnr = None
                    # Let edges incoming from parallelograms be inputs
                    if node[0] == edge[1] and dag.nodes[edge[0]]['shape_type'] == 'parallelogram':
                        inputs.append((edge[0], dag.nodes[edge[0]], inputnr))
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
                    if node[0] == edge[1] and dag.nodes[edge[0]]['shape_type'] == 'star5':
                        compositions.append((edge[0], dag.nodes[edge[0]]))
                self.actions.add(Action(action, inputs, outputs, comments, expressions, labels, compositions))

            # Create compositions from nodes
            if node[1]['shape_type'] == 'star5':
                composition = node
                inputs = list()
                outputs = list()
                comments = list()
                expressions = list()
                labels = list()
                actions = list()
                for edge in dag.edges(data=True):
                    if 'label' in edge[2]:
                        inputnr = edge[2]['label']
                    else:
                        inputnr = None
                    # Let edges incoming from arallelograms be inputs
                    if node[0] == edge[1] and dag.nodes[edge[0]]['shape_type'] == 'parallelogram':
                        inputs.append((edge[0], dag.nodes[edge[0]],inputnr))
                    # Let edges outgoing to parallelograms be outputs
                    if node[0] == edge[0] and dag.nodes[edge[1]]['shape_type'] == 'parallelogram':
                        outputs.append((edge[1], dag.nodes[edge[1]]))
                    # Let edges outgoing to roundrectangles be actions of which this is composed
                    if node[0] == edge[0] and dag.nodes[edge[1]]['shape_type'] == 'roundrectangle':
                        actions.append((edge[1], dag.nodes[edge[1]]))
                    # Let edges incoming from fat arrows be comments
                    if node[0] == edge[1] and dag.nodes[edge[0]]['shape_type'] == 'fatarrow':
                        comments.append((edge[0], dag.nodes[edge[0]]))
                    if node[0] == edge[1] and dag.nodes[edge[0]]['shape_type'] == 'octagon':
                        expressions.append((edge[0], dag.nodes[edge[0]]))
                    if node[0] == edge[1] and dag.nodes[edge[0]]['shape_type'] == 'hexagon':
                        labels.append((edge[0], dag.nodes[edge[0]]))
                    self.compositions.add(Action(composition, inputs, outputs, comments, expressions, labels, actions))

    def process_compositions(self, dag):
        # Gather all composite actions to be composed from existing actions
        #compositions = list()
        for composition in self.compositions:
            print(composition)
            subgraphnodes=set()
            for action in self.actions:
                    if composition.node in action.compositions:
                        subgraphnodes.add(action.node[0])
                        for input in action.inputs:
                            subgraphnodes.add(input[0])
                        for output in action.outputs:
                            subgraphnodes.add(output[0])
            subgraph = dag.subgraph(subgraphnodes)
            print(subgraph.edges)
            print(subgraph.nodes)


        #for action in self.actions.copy():
        #    for composition in action.compositions:
        #        compositions.append((composition, action))



    def export_to_RDF(self, file):
        rdf_g = Graph()

        # Blank node namespace
        self.namespaces.update({'_': Namespace('#')})

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
                if input[2] is not None:
                    inputnr = int(input[2])
                else:
                    inputnr = count
                p = self.namespaces['wf']['input'] + str(inputnr)
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
                print(o)
                #parse to check whether cct expression is correct
                action.ccttest(o)
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


#Read edge lebels from graphml
#xmlns:y="http://www.yworks.com/xml/graphml"
# def readEdgeLabels(file):
#     edges = []
#     tree = ET.parse(file)
#     root = tree.getroot()
#     print(root.tag)
#     for graph in root:
#         for child in graph:
#             #print(child.tag)
#             if child.tag == '{http://graphml.graphdrawing.org/xmlns}edge':
#                     edge = {}
#                     if 'source' in child.attrib.keys():
#                         edge['source']=child.attrib['source']
#                         edge['target']=child.attrib['target']
#                     for edgelabel in  child.iter("{http://www.yworks.com/xml/graphml}EdgeLabel"):
#                         if edgelabel is not None:
#                             edge['label'] = edgelabel.text
#                     edges.append(edge)
#     return edges




def process_all(indir = '../data_source/graphml/wfsemantics/', outdir = '../data_source/ttl/wfsemantics/'):
    # Export all .graphml files to .ttl files
    for file in os.listdir(indir):
        filename_parts = os.path.splitext(file)

        # Check if the file is a .graphml file
        if os.path.splitext(file)[1] == ".graphml":

            # Initialize workflow object
            wf = Workflow()

            # Import file into networkx
            networkx_dag = nx.read_graphml(indir + file)
            #print(readEdgeLabels(indir + file))

            # Convert metadata to rdflib.graph workflow metadata
            wf.update_metadata_from_networkx_dag(networkx_dag)


            # Convert data to rdflib.graph workflow action/artefact data
            wf.import_data_from_networkx_dag(networkx_dag)

            wf.process_compositions(networkx_dag)
            # Export to RDF .ttl format
            print(outdir + filename_parts[0] + '.ttl')
            wf.export_to_RDF(outdir + filename_parts[0] + '.ttl')

def main():
    process_all()
    # wf = Workflow()
    # networkx_dag = nx.read_graphml('../data_source/graphml/wfaccess.graphml')
    # wf.update_metadata_from_networkx_dag(networkx_dag)
    # wf.import_data_from_networkx_dag(networkx_dag)
    # wf.process_compositions()
    #    # Export to RDF .ttl format
    # wf.export_to_RDF(outdir + filename_parts[0] + '.ttl')
    #
    # for action in wf.actions:
    #     print(action.compositions)



main()
