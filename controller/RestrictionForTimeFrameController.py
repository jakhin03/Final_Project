from controller.NodeGenerator import ArtificialNode
from collections import defaultdict
from model.Graph import Graph
from typing import List, Tuple, Set, Optional, Dict
import numpy as np
import networkx as nx
import config 
from controller.RestrictionController import RestrictionController # Import base class

class RestrictionForTimeFrameController(RestrictionController): # Inherit from RestrictionController
    def __init__(self, graph_processor):
        super().__init__(graph_processor) # Call superclass constructor
        self.restrictions: List[Tuple[List[List[int]], List[int], int, float, float, float]] = []
        # _M, _H, _graph_processor are already set by super().__init__ via graph_processor
        self._min_gamma = 200
        self._demands = {}
        self._omega = []
        
    def get_omega(self) -> List[Tuple[int, int, int, int, int]]:
        # Getter for omega
        return self._omega
    
    def set_omega(self, omega: List[Tuple[int, int, int, int, int]]) -> None:
        # Setter for omega
        self._omega = omega
    
    # Class ArtificalNode ở đây kế thừa abstract artificialNode trong NodeGenerator
    class RestrictionArtificialNode(ArtificialNode):
        def __init__(self, id: int, label: Optional[str] = None):
            super().__init__(id, label)
            self.is_restriction_node = True
        def __repr__(self):
            return f"RestrictedArtificialNode(id={self.id}, label='{self.label}', temporary={self.temporary})"     

    def validate_restriction(self, restriction_edges: List[List[int]], timeframe: List[int], U: int) -> bool:
        # Check if restriction is valid
        if not restriction_edges or not timeframe or U < 0:
            print("Restriction không hợp lệ")
            return False
            
        if len(timeframe) != 2 or timeframe[0] > timeframe[1]:
            print("Time frame không hợp lệ")
            return False
            
        if not all(len(edge) == 2 for edge in restriction_edges):
            print("Restriction edges format không hợp lệ")
            return False
            
        return True

    def calculate_default_gamma(self, TSG, priority=1.0, k=1, min_gamma=1):
        # Calculate default penalty gamma
        if not TSG:
            return self._min_gamma
        costs = [cost for (_, _, _, _, cost) in TSG if cost is not None]
        avg_cost = np.mean(costs) if costs else 10
        gamma = k * avg_cost * max(1.0, priority)
        return max(gamma, self._min_gamma)

    def _save_restrictions_to_config(self):
        # Save the current state of self.restrictions to config
        # Ensure config attributes exist, otherwise, this won't persist without prior setup in config.py
        if hasattr(config, 'restrictions_data_cache'):
            config.restrictions_data_cache = list(self.restrictions) # Store a copy
        if hasattr(config, 'restrictions_are_set_in_cache'):
            config.restrictions_are_set_in_cache = True

    def get_restrictions(self) -> bool:
        # If restrictions are already set in config, try to load them
        if hasattr(config, 'restrictions_are_set_in_cache') and config.restrictions_are_set_in_cache:
            if hasattr(config, 'restrictions_data_cache') and config.restrictions_data_cache is not None:
                self.set_restrictions(config.restrictions_data_cache)
                return bool(self.restrictions)
            else:
                if config.restrictions_data_cache is None and hasattr(config, 'restrictions_are_set_in_cache'):
                     config.restrictions_are_set_in_cache = False # Reset to force prompt

        self.restrictions = [] # Clear existing restrictions before prompting
        try:
            L_str = input("Nhập số restrictions: ")
            if not L_str.strip(): # Handle empty input for L
                print("Số restrictions không được để trống.")
                if hasattr(config, 'restrictions_are_set_in_cache'): config.restrictions_are_set_in_cache = False
                return False

            L = int(L_str)
            if L < 0:
                print("Số restrictions phải lớn hơn hoặc bằng 0.")
                if hasattr(config, 'restrictions_are_set_in_cache'): config.restrictions_are_set_in_cache = False
                return False
            
            if L == 0:
                # User explicitly stated 0 restrictions. Cache this.
                self._save_restrictions_to_config() # self.restrictions is currently []
                return False # No restrictions to process

            for i in range(L):
                print(f"--- Nhập thông tin cho restriction {i+1}/{L} ---")
                timeframe_str = input(f"    Nhập timeframe cho restriction thứ {i+1} (vd: 3 4): ")
                if not timeframe_str.strip(): print("Timeframe không được để trống. Bỏ qua restriction này."); continue
                timeframe = list(map(int, timeframe_str.split()))

                restriction_nodes_str = input(f"    Nhập các edges cho timeframe {timeframe} (vd 3 4 5 6 là 2 edge [3,4] và [5,6]): ")
                if not restriction_nodes_str.strip(): print("Các edges không được để trống. Bỏ qua restriction này."); continue
                restriction_nodes = list(map(int, restriction_nodes_str.split()))
                
                U_str = input(f"    Nhập số lượng AGV tối đa (U) cho restriction {i+1}: ")
                if not U_str.strip(): print("U không được để trống. Bỏ qua restriction này."); continue
                U = int(U_str)

                if len(restriction_nodes) % 2 != 0 or len(restriction_nodes) < 2:
                    print("Restriction edge không hợp lệ (phải là cặp số). Bỏ qua restriction này.")
                    continue

                restriction_edges = [[restriction_nodes[j], restriction_nodes[j+1]] for j in range(0, len(restriction_nodes), 2)]

                priority_input = input(f"    Nhập priority (>=0, mặc định 1) cho restriction {i+1}: ")
                priority = 1.0
                if priority_input.strip():
                    try:
                        priority_val = float(priority_input)
                        if priority_val < 0: print("Priority không hợp lệ, dùng mặc định 1.0")
                        else: priority = priority_val
                    except ValueError: print("Priority không hợp lệ, dùng mặc định 1.0")
                
                gamma_input = input(f"    Nhập gamma (phí phạt, để trống thì tự động tính): ")
                gamma = None # Will be auto-calculated if None
                if gamma_input.strip():
                    try:
                        gamma_val = float(gamma_input)
                        if gamma_val < 1: print("Gamma quá nhỏ, dùng min_gamma = 1 (hoặc tự động tính)"); gamma = 1.0 # Or keep None for auto
                        else: gamma = gamma_val
                    except ValueError: print("Gamma không hợp lệ, sẽ tự động tính.")
                
                k_input = input(f"    Nhập hệ số k (mặc định 2, k càng lớn thì cost vi phạm càng cao) cho gamma: ")
                k_val = 2.0
                if k_input.strip():
                    try: k_val = float(k_input)
                    except ValueError: print("Hệ số k không hợp lệ, dùng mặc định 2.0")

                if self.validate_restriction(restriction_edges, timeframe, U):
                    self.restrictions.append((restriction_edges, timeframe, U, priority, gamma, k_val))
                else:
                    # validate_restriction prints its own messages
                    print(f"Restriction {i+1} không hợp lệ, đã bỏ qua.")
            
            self._save_restrictions_to_config()
            return bool(self.restrictions)

        except ValueError:
            print(f"Lỗi nhập liệu: Một trong các giá trị số không hợp lệ.")
            if hasattr(config, 'restrictions_are_set_in_cache'): config.restrictions_are_set_in_cache = False
            self.restrictions = []
            return False
        except Exception as e:
            print(f"Đã xảy ra lỗi không mong muốn: {str(e)}")
            if hasattr(config, 'restrictions_are_set_in_cache'): config.restrictions_are_set_in_cache = False
            self.restrictions = []
            return False

    def set_restrictions(self, restrictions_data: List[Tuple[List[List[int]], List[int], int, float, float, float]]) -> bool:
        # Set restrictions from data, support priority and gamma
        self.restrictions = []
        for restriction_edges, timeframe, U, priority, gamma, k in restrictions_data:
            if self.validate_restriction(restriction_edges, timeframe, U):
                self.restrictions.append((restriction_edges, timeframe, U, priority, gamma, k))
        return bool(self.restrictions)

    def restriction_parser(self, restriction: Tuple[List[List[int]], List[int], int, float, float, float]) -> Tuple[List[List[int]], int, int, int, float, float, float]:
        # Parse restriction tuple to components
        restriction_edges, [start_time_frame, end_time_frame], U, priority, gamma, k = restriction
        return restriction_edges, start_time_frame, end_time_frame, U, priority, gamma, k
    
    def _get_node_time(self, node_id: int) -> int:
        # Get time from node id
        return node_id // self._M - (1 if node_id % self._M == 0 else 0)
    
    def _get_node_coordinates(self, node_id: int) -> int:
        # Get spatial coordinate from node id
        return node_id % self._M if node_id % self._M != 0 else self._M
    
    def calculate_total_capacity(self, omega: List[Tuple[int, int, int, int, int]]) -> int:
        # Sum capacity of edges in omega
        return sum(capacity for (_, _, _, capacity, _) in omega)

    def calculate_virtual_flow(self, max_flow: int, U: int) -> int:
        # Calculate needed virtual flow
        return max(0, max_flow - U)

    def extract_weakly_connected_subgraph(self, graph: List[Tuple[int, int, int, int, int]]) -> List[List[Tuple[int, int, int, int, int]]]:
        # Get weakly connected subgraphs
        parent = {}
        
        def find(u: int) -> int:
            if parent[u] != u:
                parent[u] = find(parent[u])
            return parent[u]

        def union(u: int, v: int) -> None:
            pu, pv = find(u), find(v)
            if pu != pv:
                parent[pu] = pv

        # Initialize parent for each node
        for u, v, _, _, _ in graph:
            if u not in parent:
                parent[u] = u
            if v not in parent:
                parent[v] = v
            union(u, v)

        # Group nodes by connected components
        components = defaultdict(list)
        for edge in graph:
            root = find(edge[0])
            components[root].append(edge)

        return list(components.values())
    
    
    def identify_restricted_edges(self, restriction_edges: List[List[int]], start_time_frame: int, end_time_frame: int) -> List[Tuple[int, int, int, int, int]]:
        # Find edges in restriction time
        omega = []
        list_W = self.extract_weakly_connected_subgraph(self._graph_processor.ts_edges)
        restriction_set = {(u, v) for u, v in restriction_edges}
        print("H: ", self._H)
        for W_edges in list_W:
            for edge in W_edges:
                print("Checking edge:", edge)
                source_id, dest_id, _, capacity, cost = edge
                t1 = self._get_node_time(source_id)
                s_source = self._get_node_coordinates(source_id)
                t2 = self._get_node_time(dest_id)
                s_dest = self._get_node_coordinates(dest_id)
                base_edge = (s_source, s_dest)
                print("Source node:", s_source, "Time:", t1, "Destination node:", s_dest, "Time:", t2, "Base edge:", base_edge)
                if base_edge in restriction_set:
                    print("Edge", base_edge, "is in restriction set")
                    if (t1 <= start_time_frame < t2) or \
                       (t1 < end_time_frame <= t2) or \
                       (start_time_frame <= t1 and t2 <= end_time_frame):
                        omega.append((source_id, dest_id, 0, capacity, cost))
                        print("Added edge to omega:", (source_id, dest_id, 0, capacity, cost))   
                        
                print()             
        return omega

    def apply_restriction(self) -> None:
        if not self.get_restrictions():
            return

        edges_to_add_to_graph = set()
        edges_to_remove_from_graph = set()
        
        # Get the maximum node ID once before starting to add new nodes
        # This ensures all new IDs are unique across all restrictions
        max_node_id_val = self._graph_processor.get_max_id()

        for restriction_item in self.restrictions:
            restriction_edges_config, start_time_frame, end_time_frame, U, priority, gamma_config, k_val = self.restriction_parser(restriction_item)
            
            omega_for_this_restriction = self.identify_restricted_edges(restriction_edges_config, start_time_frame, end_time_frame)

            if not omega_for_this_restriction:
                print(f"Không tìm thấy cung nào trong restriction {restriction_item} (omega is empty).")
                # Optional: print DIMACS if needed for debugging even when omega is empty
                # dimacs_input, node_labels = self.make_dimacs_input(self._graph_processor.ts_edges, self._demands)
                # print("DIMACS input (omega empty):")
                # print(dimacs_input)
                # print("Node labels (omega empty):")
                # print(node_labels)
                continue

            # Calculate virtual_flow_needed (F - U)
            # F is the max flow through the current omega if no restrictions were applied beyond U
            current_restricted_nodes_set = self.identify_restricted_nodes(omega_for_this_restriction)
            incoming_capacity = self.calculate_incoming_capacity_for_restricted_nodes(self._graph_processor.ts_edges, current_restricted_nodes_set)
            outgoing_capacity = self.calculate_outgoing_capacity_for_restricted_nodes(self._graph_processor.ts_edges, current_restricted_nodes_set)
            
            # calculate_max_flow expects omega, incoming, outgoing.
            # Ensure these capacities are correctly interpreted by calculate_max_flow
            # to represent the total flow (F) through the omega segment.
            flow_F_through_omega = self.calculate_max_flow(omega_for_this_restriction, incoming_capacity, outgoing_capacity)
            virtual_flow_needed = self.calculate_virtual_flow(flow_F_through_omega, U) # This is max(0, F - U)

            if virtual_flow_needed <= 0:
                print(f"Restriction {restriction_item} đã thoả mãn hoặc không cần luồng ảo (F={flow_F_through_omega}, U={U}).")
                continue

            final_gamma = int(round(self.calculate_default_gamma(self._graph_processor.ts_edges, priority=priority, k=k_val if gamma_config is None else 1.0, min_gamma=self._min_gamma) if gamma_config is None else gamma_config))

            # Create global virtual source and sink for THIS restriction item
            max_node_id_val += 1
            vS_global_id = max_node_id_val
            vS_global_node = self.RestrictionArtificialNode(vS_global_id, label=f"Global_vS_Res{self.restrictions.index(restriction_item)}")
            
            max_node_id_val += 1
            vD_global_id = max_node_id_val
            vD_global_node = self.RestrictionArtificialNode(vD_global_id, label=f"Global_vD_Res{self.restrictions.index(restriction_item)}")

            self._graph_processor.check_and_add_nodes([vS_global_id, vD_global_id], is_artificial_node=True, label="GlobalRestrictionNode")
            self._graph_processor.ts_nodes.extend([vS_global_node, vD_global_node])
            if not hasattr(self._graph_processor, 'map_nodes'): self._graph_processor.map_nodes = {}
            self._graph_processor.map_nodes.update({vS_global_id: vS_global_node, vD_global_id: vD_global_node})

            for edge_orig in omega_for_this_restriction:
                u, v, l_orig, cap_orig, cost_orig = edge_orig
                edges_to_remove_from_graph.add(edge_orig) # Mark original edge for removal

                # Create intermediate virtual nodes for this edge_orig
                max_node_id_val += 1
                v_intermediate1_id = max_node_id_val
                v_i1_node = self.RestrictionArtificialNode(v_intermediate1_id, label=f"v_i1_{u}_{v}")

                max_node_id_val += 1
                v_intermediate2_id = max_node_id_val
                v_i2_node = self.RestrictionArtificialNode(v_intermediate2_id, label=f"v_i2_{u}_{v}")
                
                self._graph_processor.check_and_add_nodes([v_intermediate1_id, v_intermediate2_id], is_artificial_node=True, label="IntermediateRestrictionNode")
                self._graph_processor.ts_nodes.extend([v_i1_node, v_i2_node])
                self._graph_processor.map_nodes.update({v_intermediate1_id: v_i1_node, v_intermediate2_id: v_i2_node})

                # Add 3 new edges replacing edge_orig (for AGV flow)
                # (u, v_i1)
                edges_to_add_to_graph.add((u, v_intermediate1_id, l_orig, cap_orig, cost_orig))
                # (v_i1, v_i2)
                edges_to_add_to_graph.add((v_intermediate1_id, v_intermediate2_id, l_orig, cap_orig, 0))
                # (v_i2, v)
                edges_to_add_to_graph.add((v_intermediate2_id, v, l_orig, cap_orig, 0))

                # Add connections from global virtuals to intermediate virtuals (for virtual flow, 0 cost)
                # (vS_global, v_i1)
                edges_to_add_to_graph.add((vS_global_id, v_intermediate1_id, 0, cap_orig, 0))
                # (v_i2, vD_global)
                edges_to_add_to_graph.add((v_intermediate2_id, vD_global_id, 0, cap_orig, 0))

            # Add global escape edge for this restriction (carries virtual_flow_needed at cost gamma)
            # Lower bound 0, Upper bound is virtual_flow_needed
            edges_to_add_to_graph.add((vS_global_id, vD_global_id, 0, virtual_flow_needed, final_gamma))
            
        # After processing all restrictions, update the graph processor's edge list
        if edges_to_remove_from_graph or edges_to_add_to_graph:
            # Remove marked edges
            self._graph_processor.ts_edges = [e for e in self._graph_processor.ts_edges if e not in edges_to_remove_from_graph]
            
            # Add new edges (ensure no duplicates if somehow an edge was added by ts_edges itself)
            current_ts_edges_set = set(self._graph_processor.ts_edges)
            for new_edge in edges_to_add_to_graph:
                if new_edge not in current_ts_edges_set:
                    self._graph_processor.ts_edges.append(new_edge)
                    current_ts_edges_set.add(new_edge)
            
            # This call might be for GraphProcessor's other internal structures (like self.graph.edges from Edge objects)
            # It should process the newly added edges.
            self._graph_processor.create_set_of_edges(edges_to_add_to_graph)

        print("Đã áp dụng tất cả restrictions theo thuật toán mới thành công.")
        # self.check_restriction_violations_from_graph(self._graph_processor._graph) # If you have a way to build G

    def make_dimacs_input(self, TSG: List[Tuple[int, int, int, int, int]], demands: Dict[int, int] = {}) -> Tuple[str, Dict[int, str]]:
        """
        Generates a DIMACS format string representing the Time-Space Graph (TSG).

        Args:
            TSG: A list of tuples, where each tuple represents an edge in the TSG
                 in the format (source_id, dest_id, lower_capacity, upper_capacity, cost).
            demands: A dictionary where keys are node IDs and values are their demands.
                     Positive demand indicates a sink, negative indicates a source,
                     and zero indicates a transshipment node.

        Returns:
            A tuple containing:
                - A string in DIMACS format representing the TSG.
                - A dictionary mapping node IDs to their labels (if available).
        """
        num_nodes = 0
        edges_data = []
        node_labels = {}

        # Find all unique nodes and their labels
        all_nodes = set()
        for u, v, _, _, _ in TSG:
            all_nodes.add(u)
            all_nodes.add(v)
            if u in self._graph_processor.map_nodes:
                node_labels[u] = str(self._graph_processor.map_nodes[u].label)
            else:
                node_labels[u] = str(u)
            if v in self._graph_processor.map_nodes:
                node_labels[v] = str(self._graph_processor.map_nodes[v].label)
            else:
                node_labels[v] = str(v)

        num_nodes = len(all_nodes)
        indexed_nodes = {node: i + 1 for i, node in enumerate(sorted(list(all_nodes)))}
        reverse_indexed_nodes = {i + 1: node for node, i in indexed_nodes.items()}

        # Prepare edges in DIMACS format
        for u, v, lower, upper, cost in TSG:
            u_index = indexed_nodes[u]
            v_index = indexed_nodes[v]
            edges_data.append(f"a {u_index} {v_index} {lower} {upper} {cost}")

        # Prepare demand in DIMACS format
        demand_data = []
        for node, demand in demands.items():
            if node in indexed_nodes:
                node_index = indexed_nodes[node]
                demand_data.append(f"n {node_index} {demand}")

        # Construct the DIMACS string
        dimacs_str = f"p min {num_nodes} {len(edges_data)}\n"
        dimacs_str += "\n".join(demand_data) + "\n" if demand_data else ""
        dimacs_str += "\n".join(edges_data) + "\n"

        # Create a mapping from DIMACS internal node IDs to original node labels
        dimacs_node_labels = {i: node_labels.get(reverse_indexed_nodes[i], str(reverse_indexed_nodes[i])) for i in range(1, num_nodes + 1)}

        return dimacs_str, dimacs_node_labels

    def check_restriction_violations_from_graph(self, G, file_path='TSG.txt'):
        violations = []
        restriction_edges = []
        for u, v, data in G.edges(data=True):
            if data.get('is_restriction', False):
                U = data.get('capacity', 0)
                restriction_edges.append((u, v, U))
        # Chạy network simplex
        flowCost, flowDict = nx.network_simplex(G)
        # Kiểm tra vi phạm
        for source, dest, U in restriction_edges:
            flow = 0
            if str(source) in flowDict and str(dest) in flowDict[str(source)]:
                flow = flowDict[str(source)][str(dest)]
            if flow > U:
                n = flow - U
                print(f"Edge {source} {dest} violates {n} times (flow={flow}, U={U})")
                violations.append((source, dest, n))
        # Ghi ra file
        with open(file_path, 'w') as f:
            for source, dest, n in violations:
                f.write(f"c Edge {source} {dest} violates {n} times\n")
    
    
    def identify_restricted_nodes(self, omega: List[Tuple[int, int, int, int, int]]) -> set:
        # Identify restricted nodes in omega
        restricted_nodes = set()
        for source_id, dest_id, _, _, _ in omega:
            restricted_nodes.add(source_id)
            restricted_nodes.add(dest_id)
        return restricted_nodes
    
    
    def calculate_incoming_capacity_for_restricted_nodes(self, TSG: List[Tuple[int, int, int, int, int]] , restricted_nodes) -> defaultdict:
        # Identify restricted nodes in omega with edges come from nodes not in omega and their capacities
        restricted_nodes_incoming_capacity = defaultdict(int)
        for source_id, dest_id, _, capacity, _ in TSG:
            if dest_id in restricted_nodes  and source_id not in restricted_nodes:
                restricted_nodes_incoming_capacity[dest_id] += capacity
        return restricted_nodes_incoming_capacity
    
    def calculate_outgoing_capacity_for_restricted_nodes(self, TSG: List[Tuple[int, int, int, int, int]], restricted_nodes) -> defaultdict:
        # Identify restricted nodes in omega with edges go to nodes not in omega and their capacities
        restricted_nodes_outgoing_capacity = defaultdict(int)
        for source_id, dest_id, _, capacity, _ in TSG:
            if source_id in restricted_nodes and dest_id not in restricted_nodes:
                restricted_nodes_outgoing_capacity[source_id] += capacity
                
        return restricted_nodes_outgoing_capacity
    
    
    def calculate_max_flow(self , omega: List[Tuple[int, int, int, int, int]] , restricted_nodes_incoming_capacity , restricted_nodes_outgoing_capacity) -> int:
        # Calculate max flow F
        
        # Build graph
        G = nx.DiGraph()
        # Ensure virtual source and sink nodes exist in the graph
        G.add_node("vS")
        G.add_node("vT")

        for source_id, dest_id, _, capacity, _ in omega:
            G.add_edge(source_id, dest_id, capacity=capacity)
            
        # Add incoming edges for restricted nodes
        for node_id, capacity in restricted_nodes_incoming_capacity.items():
            G.add_edge("vS", node_id , capacity=capacity)
        
        # Add outgoing edges for restricted nodes
        for node_id, capacity in restricted_nodes_outgoing_capacity.items():
            G.add_edge(node_id, "vT", capacity=capacity)
                        
        return nx.maximum_flow_value(G, "vS", "vT")
    
    
    
    def generate_restriction_edges(self, start_node, end_node, nodes, adj_edges):
        pass
