from controller.GraphProcessor import GraphProcessor
from controller.RestrictionForTimeFrameController import RestrictionForTimeFrameController
import networkx as nx
from unittest.mock import patch


def read_dimac_file(file_path = "TSG.txt"):
    TSG = list()
    with open(file_path, 'r') as file:
        for line in file:
            parts = line.split()
            if parts[0] == 'a':
                ID1 = int(parts[1])
                ID2 = int(parts[2])
                L = int(parts[3])
                U = int(parts[4])
                C = int(parts[5])
                TSG.append((ID1, ID2,L, U, C))
    return TSG
result = 4


graph_processor = GraphProcessor()
with patch('builtins.input' , side_effect=["QuardNodes.txt","10" ,"0" , "1","1","1","1","2 7" , "1 2 2 3", "1"]):
    graph_processor.use_in_main()

 
restriction = graph_processor.restriction_for_timeframe_controller
TSG = read_dimac_file("TSG.txt")   

omega = restriction.identify_restricted_edges( [[1,2],[2,3]] , 2, 7 )
restriction_nodes = restriction.indentify_restricted_nodes( omega )
incoming_capacity_for_restricted_nodes = restriction.calculate_incoming_capacity_for_restricted_nodes( TSG, restriction_nodes)
outgoing_capacity_for_restricted_nodes = restriction.calculate_outgoing_capacity_for_restricted_nodes( TSG , restriction_nodes)
max_flow = restriction.calulate_max_flow( omega , incoming_capacity_for_restricted_nodes , outgoing_capacity_for_restricted_nodes )
assert max_flow == result, f"Max flow should be {result}, but got {max_flow}"
print(f"Test passed! Max flow is {max_flow}")