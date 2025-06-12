from controller.GraphProcessor import GraphProcessor
import networkx as nx
from unittest.mock import patch
from model.Graph import Graph


result = 4


graph_processor = GraphProcessor() 
with patch('builtins.input' , side_effect=["QuardNodes.txt","10" ,"0" , "1","1","1","2 5", "4 1 1 2", "1", "1","","2"]):
    graph_processor.use_in_main()


restriction = graph_processor.restriction_for_timeframe_controller

omega = restriction.get_omega()
assert len(omega) == 1, "Omega should contain exactly one graph, but it contains: " + str(len(omega))
omega = omega[0]
restriction_nodes = restriction.identify_restricted_nodes( omega )
restriction.remove_artificial_artifact()
incoming_capacity_for_restricted_nodes = restriction.calculate_incoming_capacity_for_restricted_nodes( graph_processor.ts_edges, restriction_nodes)
outgoing_capacity_for_restricted_nodes = restriction.calculate_outgoing_capacity_for_restricted_nodes( graph_processor.ts_edges , restriction_nodes)
max_flow = restriction.calculate_max_flow( omega , incoming_capacity_for_restricted_nodes , outgoing_capacity_for_restricted_nodes )
assert max_flow == result, f"Max flow should be {result}, but got {max_flow}"
print(f"Test passed! Max flow is {max_flow}")