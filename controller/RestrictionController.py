import os
import pdb
from collections import defaultdict
from abc import ABC, abstractmethod # Import ABC and abstractmethod

class RestrictionController(ABC): # Inherit from ABC
    def __init__(self, graph_processor):
        self.restriction_edges_store = defaultdict(list) # Renamed to avoid conflict if subclass has self.restrictions
        self.alpha = graph_processor.alpha
        self.beta = graph_processor.beta
        self.gamma = graph_processor.gamma
        self._H = graph_processor.H 
        self.ur = graph_processor.ur # Assuming ur is a property of graph_processor if not set directly
        self._M = graph_processor.M
        self._graph_processor = graph_processor

    @abstractmethod
    def generate_restriction_edges(self, start_node, end_node, nodes, adj_edges):
        """
        Generates and applies specific restriction edges, often called during graph construction.
        This method must be implemented by subclasses.
        """
        pass

    @abstractmethod
    def apply_restriction(self):
        """
        Applies the main restriction logic for the controller.
        For RestrictionForTimeFrameController, this involves handling timeframes,
        user inputs, and modifying the graph with virtual nodes/edges.
        This method must be implemented by subclasses.
        """
        pass
    
    # def add_nodes_and__re_node(self, forward_to_a_s, rise_from_a_t, restriction, a_s, a_t):
    #     #pdb.set_trace()
    #     #if( isinstance(node, RestrictionNode)):
    #     key = tuple(restriction)
    #     if(key not in self.restriction_edges_store): # Use renamed attribute
    #         self.restriction_edges_store[key] = []
    #     found = False
    #     for to_a_s, from_a_t, _, _ in self.restriction_edges_store[key]: # Use renamed attribute
    #         if(to_a_s == forward_to_a_s and from_a_t == rise_from_a_t):
    #             found = True
    #             break
    #     if(not found):
    #         self.restriction_edges_store[key].append([forward_to_a_s, rise_from_a_t, a_s, a_t]) # Use renamed attribute

    # def remove_restriction_edges(self, key):
    #     if(key in self.restriction_edges_store): # Use renamed attribute
    #         del self.restriction_edges_store[key] # Use renamed attribute
    # # ... (other commented out methods)