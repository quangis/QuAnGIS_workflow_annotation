import networkx as nx
from hubs import *
from workflow_turtling import *

# Libraries for parsing CCT expressions
from cct import cct
import transforge as tf


def main():
    g = nx.read_graphml('../data_source/graphml/wfaccess.graphml')
    add_context(g, 'askdlflakjs')
    for node in g.nodes(data=True):
        print(node)
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
    wf.generalize()
    wf.to_rdf('../data_source/graphml/wfaccess_test2.ttl')


main()
