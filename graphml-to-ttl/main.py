import networkx as nx
from hubs import *
from workflow_turtling import *
import os

# Libraries for parsing CCT expressions
from cct import cct
import transforge as tf


def main():
    """g = nx.read_graphml('../data_source/graphml/wfsemantics/wfaccess.graphml')
    add_context_edges(g, 'wfaccess')

    # Remove redundant coordinate information from nodes
    actions = []
    artefacts = []
    for node in g.nodes():
        if 'x' in g.nodes[node]:
            del g.nodes[node]['x']
        if 'y' in g.nodes[node]:
            del g.nodes[node]['y']
        if g.nodes[node]['shape_type'] == 'roundrectangle':
            actions.append(Action(node, g))
        if g.nodes[node]['shape_type'] == 'parallelogram':
            artefacts.append(Artefact(node, g))
    """
    #wf = Workflow(actions, g)
    #wf.generalize()
    #wf.to_rdf('../data_source/graphml/wfsemantics/wfaccess_test.ttl')

    current_dir = os.getcwd()
    input_folder = os.path.join(current_dir, "..\data_source\graphml\wfsemantics")
    output_folder = os.path.join(current_dir, "..\data_source\\ttl\\general\\")

    for filename in os.listdir(input_folder):
        f = os.path.join(input_folder, filename)
        head, tail = os.path.split(f)
        # checking if it is a file
        if f.endswith('wfcrime_prep.graphml'):  # This wf has multiple final outputs
            continue
        elif tail.split('.')[1] == 'graphml':
            g = nx.read_graphml(f)
            add_context_edges(g)

            # Remove redundant coordinate information from nodes
            actions = []
            artefacts = []
            for node in g.nodes():
                if 'x' in g.nodes[node]:
                    del g.nodes[node]['x']
                if 'y' in g.nodes[node]:
                    del g.nodes[node]['y']
                if g.nodes[node]['shape_type'] == 'roundrectangle':
                    actions.append(Action(node, g))
                if g.nodes[node]['shape_type'] == 'parallelogram':
                    artefacts.append(Artefact(node, g))

            wf = Workflow(actions, g)
            #wf.specify()
            wf.generalize()
            wf.to_rdf(output_folder + tail.replace('graphml', 'ttl'))
            Hub.clear_cache()


main()
