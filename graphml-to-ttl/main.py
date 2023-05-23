import networkx as nx
from artefactions import *
import os


def main():
    current_dir = os.getcwd()
    input_folder = os.path.join(current_dir, "../data_source/graphml/wfsemantics/")
    output_folder = os.path.join(current_dir, "../data_source/ttl/")

    for file in os.listdir(input_folder):
        if file.endswith('.graphml'):
            g = nx.read_graphml(input_folder + file)
            add_context_edges(g)
            check_graph(g)
            print(file.replace('.graphml', ''))
            wf_node = [x for x, y in g.nodes(data=True) if y['label'] == file.replace('.graphml', '')][0]
            wf = Action(wf_node, g)
            ttl_file = file.replace('.graphml', '.ttl')
            wf.to_ttl(output_folder + ttl_file)
            print(output_folder + ttl_file)
            clear_all_caches()

    '''
    g = nx.read_graphml('D:\PhD\Github\QuAnGIS_workflow_annotation\data_source\graphml\wfsemantics\wfcrime_exposure.graphml')
    add_context_edges(g)
    wf_node = [x for x, y in g.nodes(data=True) if y['label'] == wf_name][0]
    wf = Action(wf_node, g)
    wf.to_ttl('D:\PhD\Github\QuAnGIS_workflow_annotation\data_source\graphml\wfsemantics\wfcrime_exposure.ttl')
    '''

main()
