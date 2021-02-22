import logging
import tempfile
from scripts.graph.networkx_graph_wrapper import get_graph_from_gexf, get_node_connected_component
from model import TlshClusterAnalysis, TlshHash


def start_find_similar_hashes_by_graph(cluster_analysis_id, tlsh_hash_id):
    logging.info(f"{tlsh_hash_id}\t{cluster_analysis_id}")
    tlsh_hash = TlshHash.objects.get(pk=tlsh_hash_id)
    cluster_analysis = TlshClusterAnalysis.objects.get(pk=cluster_analysis_id)
    graph_temp_file = tempfile.NamedTemporaryFile()
    graph_temp_file.write(cluster_analysis.gexf_file.read())
    graph = get_graph_from_gexf(graph_temp_file.name)
    component_set = get_node_connected_component(graph, f"{tlsh_hash.filename}:{tlsh_hash.id}")
    return component_set



