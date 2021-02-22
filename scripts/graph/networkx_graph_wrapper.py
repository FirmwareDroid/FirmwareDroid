import logging
import tempfile
import networkx as nx


def create_weighted_graph_file(weighted_edge_dictionary):
    """
    Create first a graph and then a gexf from the graph.
    :param weighted_edge_dictionary: dict(str, dict(str, int)) - dictionary structure with edges and weight.
    :return: temporary file that includes the graph in gexf format.
    """
    logging.info("Create gexf graph file")
    graph = create_weighted_graph(weighted_edge_dictionary)
    return graph_to_gexf_file(graph)


def create_weighted_graph(weighted_edge_dictionary):
    """
    Creates a weighted networkx graph with labels.
    :param weighted_edge_dictionary: dict(str, dict(str, int)) - dictionary structure with edges and weight.
    :return: class:'nx.Graph'
    """
    graph = nx.Graph()
    for node_a_label, node_a_dict in weighted_edge_dictionary.items():
        for node_b_label, node_b_value in node_a_dict.items():
            add_edge_to_graph(graph, node_a_label, node_b_label, node_b_value)
    pos = nx.spring_layout(graph)
    nx.draw_networkx_nodes(graph, pos, node_size=700)
    nx.draw_networkx_labels(graph, pos, font_size=20, font_family="sans-serif")
    return graph


def add_edge_to_graph(graph, node_a_label, node_b_label, weight):
    """
    Add a weighted edge to a graph. Only positive weights (>0) are allowed.
    :param graph: class:'nx.Graph'
    :param node_a_label: str - label of the node
    :param node_b_label: str - label of the node
    :param weight: int - weight of the edge
    """
    if weight <= 0:
        weight = 0.00000001
    graph.add_edge(node_a_label, node_b_label, weight=weight)


def graph_to_gexf_file(graph):
    """
    Creates temporary gexf file.
    :param graph: class:'nx.Graph'
    :return: temporary file in gexf format.
    """
    tmp_file = tempfile.NamedTemporaryFile()
    nx.write_gexf(graph, tmp_file.name)
    return tmp_file


def graph_to_graphml(graph):
    tmp_file = tempfile.NamedTemporaryFile()
    nx.write_graphml(graph, tmp_file.name)
    return tmp_file


def get_graph_from_gexf(gexf_file_path):
    """
    Create a graph from a gexf file.
    :param gexf_file_path: str - path of the gexf file.
    :return: class:'nx.Graph'
    """
    return nx.readwrite.read_gexf(gexf_file_path)


def get_node_connected_component(graph, node_label):
    """
    Gets all nodes that are connected to the node label in the graph.
    :param graph: class:'nx.Graph'
    :param node_label: str - node to search for.
    :return: set - A set of nodes in the component of the graph containing the node label
    """
    return nx.algorithms.components.connected.node_connected_component(graph, node_label)
