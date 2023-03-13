import networkx as nx
import rdflib as rdf
import os
from hubs import *

# Libraries for parsing CCT expressions
from cct import cct
import transforge as tf


def main():
    g = nx.read_graphml('../data_source/graphml/wfaccess.graphml')
    add_context(g, 'askdlflakjs')
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

    for action in actions:
        print(action)


main()
