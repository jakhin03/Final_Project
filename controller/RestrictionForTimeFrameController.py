from controller.NodeGenerator import ArtificialNode
from collections import defaultdict
from model.Graph import Graph
from typing import List, Tuple, Set, Optional, Dict
import numpy as np
import networkx as nx
import config
from controller.RestrictionController import RestrictionController
from gamma_analysis.integrated_gamma_control import GammaControlIntegrator

class RestrictionForTimeFrameController(RestrictionController):
    def __init__(self, graph_processor):
        super().__init__(graph_processor)
        self.restrictions: List[Tuple[List[List[int]], List[int], int, float, Optional[float], float]] = []
        self._min_gamma = 200
        self._demands = {} # Mặc dù không dùng trong thuật toán mới, giữ lại có thể hữu ích cho debug hoặc so sánh
        self._omega = []
        
        # --- MERGED FROM max_flow ---
        self._all_additional_edges: List[Tuple[int, int, int, int, int]] = []
        self._all_additional_nodes: Set[int] = set()
        
        # --- GAMMA CONTROL INTEGRATION ---
        self.gamma_integrator = None
        self.last_escape_edges = []
        self.last_violations = []
        
        # --- VIRTUAL FLOW MAPPING ---
        # Map virtual node IDs to their virtual flow values
        # Format: {vS_global_id: virtual_flow_needed, vD_global_id: -virtual_flow_needed}
        self._virtual_node_demands = {}

    # --- MERGED FROM max_flow ---
    def get_all_additional_nodes(self) -> Set[int]:
        return self._all_additional_nodes
    
    def set_all_additional_nodes(self, nodes: Set[int]) -> None:
        self._all_additional_nodes = nodes
        
    def get_all_additional_edges(self) -> List[Tuple[int, int, int, int, int]]:
        return self._all_additional_edges
    
    def set_all_additional_edges(self, edges: List[Tuple[int, int, int, int, int]]) -> None:
        self._all_additional_edges = edges

    # --- MERGED FROM max_flow---
    def remove_artificial_artifact(self):
        """
        Khôi phục lại đồ thị về trạng thái trước khi áp dụng ràng buộc
        bằng cách xóa các nút và cung ảo đã được thêm vào.
        """
        print("[DEBUG] remove_artificial_artifact: Starting cleanup process")
        
        additional_nodes_ids = self.get_all_additional_nodes()
        additional_edges_tuples = self.get_all_additional_edges()
        
        print(f"[DEBUG] Will remove {len(additional_nodes_ids)} additional nodes: {sorted(additional_nodes_ids)}")
        print(f"[DEBUG] Will remove {len(additional_edges_tuples)} additional edges")

        # Xóa các nút ảo
        if additional_nodes_ids:
            original_node_count = len(self._graph_processor.ts_nodes)
            self._graph_processor.ts_nodes = [
                node for node in self._graph_processor.ts_nodes
                if node.id not in additional_nodes_ids
            ]
            removed_nodes = original_node_count - len(self._graph_processor.ts_nodes)
            print(f"[DEBUG] Removed {removed_nodes} nodes from ts_nodes")
            
            removed_map_nodes = 0
            for node_id in additional_nodes_ids:
                if node_id in self._graph_processor.map_nodes:
                    self._graph_processor.map_nodes.pop(node_id, None)
                    removed_map_nodes += 1
            print(f"[DEBUG] Removed {removed_map_nodes} nodes from map_nodes")

        # Xóa các cung ảo
        if additional_edges_tuples:
            # Tạo một set từ tuple của các cung ảo để tìm kiếm nhanh hơn
            additional_edges_set = { (e[0], e[1]) for e in additional_edges_tuples }
            print(f"[DEBUG] Additional edges set: {additional_edges_set}")
            
            # Xóa từ self._graph_processor.ts_edges (list of tuples)
            original_edge_count = len(self._graph_processor.ts_edges)
            self._graph_processor.ts_edges = [
                edge for edge in self._graph_processor.ts_edges
                if (edge[0], edge[1]) not in additional_edges_set
            ]
            removed_edges = original_edge_count - len(self._graph_processor.ts_edges)
            print(f"[DEBUG] Removed {removed_edges} edges from ts_edges")
            
            # Xóa từ self._graph_processor.tsedges (list of Edge objects)
            if hasattr(self._graph_processor, 'tsedges'):
                original_tsedges_count = len(self._graph_processor.tsedges)
                self._graph_processor.tsedges = [
                    edge_obj for edge_obj in self._graph_processor.tsedges
                    if hasattr(edge_obj, 'start_node') and (edge_obj.start_node.id, edge_obj.end_node.id) not in additional_edges_set
                ]
                removed_tsedges = original_tsedges_count - len(self._graph_processor.tsedges)
                print(f"[DEBUG] Removed {removed_tsedges} edges from tsedges")

        # Khôi phục các cung gốc đã bị xóa
        original_edges_to_re_add = {
            edge for edge in self._omega
            if any((e[0], e[1]) in additional_edges_set for e in self.get_all_additional_edges()) # Heuristic to find which omega was processed
        }
        if original_edges_to_re_add:
            print(f"[DEBUG] Re-adding {len(original_edges_to_re_add)} original omega edges")
            self._graph_processor.ts_edges.extend(list(original_edges_to_re_add))
            self._graph_processor.create_set_of_edges(original_edges_to_re_add)

        # Reset lại trạng thái
        self.set_all_additional_nodes(set())
        self.set_all_additional_edges([])
        self._omega = []
        self._virtual_node_demands = {}  # Clear virtual node demands
        
        print(f"[DEBUG] Cleanup completed - omega cleared, virtual demands cleared")
        print("[CLEANUP] Successfully removed all artificial nodes and edges")


    
    class RestrictionArtificialNode(ArtificialNode):
        def __init__(self, id: int, label: Optional[str] = None):
            super().__init__(id, label)
            self.is_restriction_node = True
        def __repr__(self):
            return f"RestrictedArtificialNode(id={self.id}, label='{self.label}', temporary={self.temporary})"

    def validate_restriction(self, restriction_edges: List[List[int]], timeframe: List[int], U: int) -> bool:
        if not restriction_edges or not timeframe or U < 0:
            print("[ERROR] Validation failed: Missing basic information")
            return False
        if len(timeframe) != 2 or timeframe[0] > timeframe[1]:
            print("[ERROR] Validation failed: Invalid timeframe format (must have 2 values, start <= end)")
            return False
        if not all(len(edge) == 2 for edge in restriction_edges):
            print("[ERROR] Validation failed: Invalid edge format (each edge must have 2 nodes)")
            return False
        return True

    def calculate_default_gamma(self, TSG, priority=1.0, k=1, min_gamma=200):
        if not TSG:
            print(f"[DEBUG] calculate_default_gamma: TSG is empty, returning min_gamma={min_gamma}")
            return min_gamma
        costs = [cost for (_, _, _, _, cost) in TSG if cost is not None]
        avg_cost = np.mean(costs) if costs else 10
        gamma = k * avg_cost * max(1.0, priority)
        final_gamma = max(gamma, min_gamma)
        print(f"[DEBUG] calculate_default_gamma: costs_count={len(costs)}, avg_cost={avg_cost}, k={k}, priority={priority}, calculated_gamma={gamma}, final_gamma={final_gamma}")
        return final_gamma

    def _save_restrictions_to_config(self):
        if hasattr(config, 'restrictions_data_cache'):
            config.restrictions_data_cache = list(self.restrictions)
        if hasattr(config, 'restrictions_are_set_in_cache'):
            config.restrictions_are_set_in_cache = True

    def get_restrictions(self) -> bool:
        if hasattr(config, 'restrictions_are_set_in_cache') and config.restrictions_are_set_in_cache:
            if hasattr(config, 'restrictions_data_cache'):
                self.set_restrictions(config.restrictions_data_cache if config.restrictions_data_cache is not None else [])
                return bool(self.restrictions)
            config.restrictions_are_set_in_cache = False

        print("[Restriction Config] Setting up traffic restrictions...")

        self.restrictions = []
        try:
            L_str = input("\nEnter number of restrictions (leave empty for none): ")
            if not L_str.strip():
                print("[Restriction Config] No restrictions specified")
                self._save_restrictions_to_config()
                return False

            L = int(L_str)
            if L == 0:
                print("[Restriction Config] Zero restrictions specified")
                self._save_restrictions_to_config()
                return False

            print(f"[Restriction Config] Setting up {L} restrictions")
            # ...existing code...

            for i in range(L):
                print(f"[Restriction Config] Input {i+1}/{L}")
                
                timeframe_str = input(f"    Timeframe (e.g., '3 4'): ")
                if not timeframe_str.strip(): 
                    print("[Restriction Config] WARNING: Timeframe cannot be empty. Skipping")
                    continue
                timeframe = list(map(int, timeframe_str.split()))

                restriction_nodes_str = input(f"    Restricted edges for timeframe {timeframe} (e.g., '3 4 5 6' for edges [3,4] and [5,6]): ")
                if not restriction_nodes_str.strip(): 
                    print("[Restriction Config] WARNING: Edges cannot be empty. Skipping")
                    continue
                restriction_nodes = list(map(int, restriction_nodes_str.split()))
                
                U_str = input(f"    Maximum AGVs allowed (U): ")
                if not U_str.strip(): 
                    print("[Restriction Config] WARNING: Maximum AGVs (U) cannot be empty. Skipping")
                    continue
                U = int(U_str)

                if len(restriction_nodes) % 2 != 0 or len(restriction_nodes) < 2:
                    print("[Restriction Config] ERROR: Invalid edge format. Skipping")
                    continue

                restriction_edges = [[restriction_nodes[j], restriction_nodes[j+1]] for j in range(0, len(restriction_nodes), 2)]

                priority_input = input(f"    Priority (>=0, default=1): ")
                priority = 1.0
                if priority_input.strip():
                    try:
                        priority_val = float(priority_input)
                        if priority_val < 0: 
                            print("[Restriction Config] WARNING: Invalid priority, using default 1.0")
                        else: priority = priority_val
                    except ValueError: 
                        print("[Restriction Config] WARNING: Invalid priority format, using default 1.0")
                
                gamma_input = input(f"    Penalty cost gamma (leave empty for auto-calculation): ")
                gamma = None # Will be auto-calculated if None
                if gamma_input.strip():
                    try:
                        gamma_val = float(gamma_input)
                        if gamma_val < 1: 
                            print("[Restriction Config] WARNING: Gamma too small, using minimum 1.0")
                            gamma = 1.0
                        else: gamma = gamma_val
                    except ValueError: 
                        print("[Restriction Config] WARNING: Invalid gamma format, will auto-calculate")
                
                k_input = input(f"    K-factor for gamma calculation (default=2, higher K = higher violation cost): ")
                k_val = 2.0
                if k_input.strip():
                    try: k_val = float(k_input)
                    except ValueError: 
                        print("[Restriction Config] WARNING: Invalid K-factor format, using default 2.0")

                if self.validate_restriction(restriction_edges, timeframe, U):
                    self.restrictions.append((restriction_edges, timeframe, U, priority, gamma, k_val))
                    print(f"[Restriction Config] Restriction {i+1} added successfully")
                else:
                    # validate_restriction prints its own messages
                    print(f"[Restriction Config] Restriction {i+1} validation failed, skipped")
            self._save_restrictions_to_config()
            print(f"[Restriction Config] Setup completed: {len(self.restrictions)} restrictions added")
            return bool(self.restrictions)
        except (ValueError, Exception) as e:
            print(f"[FATAL ERROR] Input error: {e}")
            if hasattr(config, 'restrictions_are_set_in_cache'): config.restrictions_are_set_in_cache = False
            self.restrictions = []
            return False

    def set_restrictions(self, restrictions_data: List[Tuple[List[List[int]], List[int], int, float, Optional[float], float]]):
        self.restrictions = []
        for restriction_edges, timeframe, U, priority, gamma, k in restrictions_data:
            if self.validate_restriction(restriction_edges, timeframe, U):
                self.restrictions.append((restriction_edges, timeframe, U, priority, gamma, k))
        return bool(self.restrictions)

    def restriction_parser(self, restriction: Tuple) -> Tuple:
        return restriction[0], restriction[1][0], restriction[1][1], restriction[2], restriction[3], restriction[4], restriction[5]
    
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
        virtual_flow = max(0, max_flow - U)
        print(f"[DEBUG] calculate_virtual_flow: max_flow={max_flow}, U={U}, virtual_flow={virtual_flow}")
        return virtual_flow

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

    def identify_restricted_edges(self, restriction_edges, start_time_frame, end_time_frame):
        print(f"[DEBUG] identify_restricted_edges: restriction_edges={restriction_edges}, timeframe=[{start_time_frame}, {end_time_frame}]")
        
        omega = []
        restriction_set = {(u, v) for u, v in restriction_edges}
        print(f"[DEBUG] restriction_set: {restriction_set}")
        
        total_edges_checked = 0
        matching_edges = 0
        
        for edge_tuple in self._graph_processor.ts_edges:
            total_edges_checked += 1
            source_id, dest_id, _, capacity, cost = edge_tuple
            t1 = self._get_node_time(source_id)
            t2 = self._get_node_time(dest_id)
            s_source = self._get_node_coordinates(source_id)
            s_dest = self._get_node_coordinates(dest_id)
            base_edge = (s_source, s_dest)

            if base_edge in restriction_set:
                matching_edges += 1
                time_intersects = (t1 < end_time_frame) and (t2 > start_time_frame)
                print(f"[DEBUG] Edge ({source_id}, {dest_id}) -> base_edge={base_edge}, times=({t1}, {t2}), time_intersects={time_intersects}")
                
                if time_intersects:
                    omega.append((source_id, dest_id, 0, capacity, cost))
                    print(f"[DEBUG] Added to omega: ({source_id}, {dest_id}, 0, {capacity}, {cost})")
        
        print(f"[DEBUG] identify_restricted_edges result: checked {total_edges_checked} edges, found {matching_edges} matching edges, omega size: {len(omega)}")
        return omega
    
    def identify_restricted_nodes(self, omega: List[Tuple[int, int, int, int, int]]) -> set:
        # Identify restricted nodes in omega
        print(f"[DEBUG] identify_restricted_nodes: omega size = {len(omega)}")
        
        restricted_nodes = set()
        for source_id, dest_id, _, _, _ in omega:
            restricted_nodes.add(source_id)
            restricted_nodes.add(dest_id)
            print(f"[DEBUG] Processing edge ({source_id}, {dest_id})")
        
        print(f"[DEBUG] identify_restricted_nodes result: {len(restricted_nodes)} nodes = {sorted(restricted_nodes)}")
        return restricted_nodes
        
    def calculate_incoming_capacity_for_restricted_nodes(self, TSG: List[Tuple[int, int, int, int, int]] , restricted_nodes) -> defaultdict:
        # Identify restricted nodes in omega with edges come from nodes not in omega and their capacities
        print(f"[DEBUG] calculate_incoming_capacity: restricted_nodes={sorted(restricted_nodes)}, TSG size={len(TSG)}")
        
        restricted_nodes_incoming_capacity = defaultdict(int)
        incoming_edges_found = 0
        
        for source_id, dest_id, _, capacity, _ in TSG:
            if dest_id in restricted_nodes  and source_id not in restricted_nodes:
                restricted_nodes_incoming_capacity[dest_id] += capacity
                incoming_edges_found += 1
                print(f"[DEBUG] Incoming edge: ({source_id}, {dest_id}) capacity={capacity}")
        
        print(f"[DEBUG] calculate_incoming_capacity result: found {incoming_edges_found} incoming edges")
        for node_id, capacity in restricted_nodes_incoming_capacity.items():
            print(f"[DEBUG] Node {node_id} total incoming capacity: {capacity}")
        
        return restricted_nodes_incoming_capacity
    
    def calculate_outgoing_capacity_for_restricted_nodes(self, TSG: List[Tuple[int, int, int, int, int]], restricted_nodes) -> defaultdict:
        # Identify restricted nodes in omega with edges go to nodes not in omega and their capacities
        print(f"[DEBUG] calculate_outgoing_capacity: restricted_nodes={sorted(restricted_nodes)}, TSG size={len(TSG)}")
        
        restricted_nodes_outgoing_capacity = defaultdict(int)
        outgoing_edges_found = 0
        
        for source_id, dest_id, _, capacity, _ in TSG:
            if source_id in restricted_nodes and dest_id not in restricted_nodes:
                restricted_nodes_outgoing_capacity[source_id] += capacity
                outgoing_edges_found += 1
                print(f"[DEBUG] Outgoing edge: ({source_id}, {dest_id}) capacity={capacity}")
                
        print(f"[DEBUG] calculate_outgoing_capacity result: found {outgoing_edges_found} outgoing edges")
        for node_id, capacity in restricted_nodes_outgoing_capacity.items():
            print(f"[DEBUG] Node {node_id} total outgoing capacity: {capacity}")
        
        return restricted_nodes_outgoing_capacity
    
    def calculate_max_flow(self , omega: List[Tuple[int, int, int, int, int]] , restricted_nodes_incoming_capacity , restricted_nodes_outgoing_capacity) -> int:
        # Calculate max flow F
        print(f"[DEBUG] calculate_max_flow: omega size={len(omega)}")
        print(f"[DEBUG] incoming capacity nodes: {len(restricted_nodes_incoming_capacity)}")
        print(f"[DEBUG] outgoing capacity nodes: {len(restricted_nodes_outgoing_capacity)}")
        
        # Build graph
        G = nx.DiGraph()
        # Ensure virtual source and sink nodes exist in the graph
        G.add_node("vS")
        G.add_node("vT")
        print(f"[DEBUG] Added virtual source 'vS' and sink 'vT' nodes")

        # Add omega edges
        omega_edges_added = 0
        for source_id, dest_id, _, capacity, _ in omega:
            G.add_edge(source_id, dest_id, capacity=capacity)
            omega_edges_added += 1
            print(f"[DEBUG] Added omega edge: ({source_id}, {dest_id}) capacity={capacity}")
        
        print(f"[DEBUG] Added {omega_edges_added} omega edges to max flow graph")
            
        # Add incoming edges for restricted nodes
        incoming_edges_added = 0
        for node_id, capacity in restricted_nodes_incoming_capacity.items():
            G.add_edge("vS", node_id , capacity=capacity)
            incoming_edges_added += 1
            print(f"[DEBUG] Added incoming edge: (vS, {node_id}) capacity={capacity}")
        
        print(f"[DEBUG] Added {incoming_edges_added} incoming edges from vS")
        
        # Add outgoing edges for restricted nodes
        outgoing_edges_added = 0
        for node_id, capacity in restricted_nodes_outgoing_capacity.items():
            G.add_edge(node_id, "vT", capacity=capacity)
            outgoing_edges_added += 1
            print(f"[DEBUG] Added outgoing edge: ({node_id}, vT) capacity={capacity}")
        
        print(f"[DEBUG] Added {outgoing_edges_added} outgoing edges to vT")
        
        # Calculate max flow
        max_flow_value = nx.maximum_flow_value(G, "vS", "vT")
        print(f"[DEBUG] Maximum flow calculated: {max_flow_value}")
        
        return max_flow_value

    def apply_restriction(self) -> None:
        print("[Restriction] Applying restrictions...")
        
        if not self.get_restrictions():
            return
        
        # Reset lại trạng thái nếu hàm được gọi lại
        if self._all_additional_nodes or self._all_additional_edges:
            self.remove_artificial_artifact()

        max_node_id_val = self._graph_processor.get_max_id()
        processed_restrictions = 0

        for idx, restriction_item in enumerate(self.restrictions):
            print(f"[DEBUG] Processing restriction {idx + 1}/{len(self.restrictions)}")
            
            restriction_edges_config, start_time_frame, end_time_frame, U, priority, gamma_config, k_val = self.restriction_parser(restriction_item)
            print(f"[DEBUG] Restriction {idx + 1}: timeframe=[{start_time_frame}, {end_time_frame}], U={U}, priority={priority}, gamma={gamma_config}, k={k_val}")
            print(f"[DEBUG] Restriction {idx + 1}: edges_config={restriction_edges_config}")
            
            omega_for_this_restriction = self.identify_restricted_edges(restriction_edges_config, start_time_frame, end_time_frame)
            if not omega_for_this_restriction:
                print(f"[DEBUG] Restriction {idx + 1}: No omega edges found, skipping")
                continue
            
            print(f"[DEBUG] Restriction {idx + 1}: Found {len(omega_for_this_restriction)} omega edges")
            
            # Lưu lại omega để có thể khôi phục cung gốc khi dọn dẹp
            self._omega.extend(omega_for_this_restriction)

            current_restricted_nodes_set = self.identify_restricted_nodes(omega_for_this_restriction)
            print(f"[DEBUG] Restriction {idx + 1}: Restricted nodes: {sorted(current_restricted_nodes_set)}")
            
            incoming_capacity = self.calculate_incoming_capacity_for_restricted_nodes(self._graph_processor.ts_edges, current_restricted_nodes_set)
            outgoing_capacity = self.calculate_outgoing_capacity_for_restricted_nodes(self._graph_processor.ts_edges, current_restricted_nodes_set)
            
            flow_F_through_omega = self.calculate_max_flow(omega_for_this_restriction, incoming_capacity, outgoing_capacity)
            virtual_flow_needed = self.calculate_virtual_flow(flow_F_through_omega, U)
            
            print(f"[DEBUG] Restriction {idx + 1}: Max flow F={flow_F_through_omega}, U={U}, virtual_flow_needed={virtual_flow_needed}")

            if virtual_flow_needed <= 0:
                print(f"[DEBUG] Restriction {idx + 1}: No virtual flow needed, skipping")
                continue

            final_gamma = int(round(gamma_config if gamma_config is not None else self.calculate_default_gamma(self._graph_processor.ts_edges, priority, k_val, self._min_gamma)))
            print(f"[DEBUG] Restriction {idx + 1}: Final gamma={final_gamma}")
            
            # Tạo nút ảo toàn cục cho ràng buộc này
            max_node_id_val += 1
            vS_global_id = max_node_id_val
            vS_global_node = self.RestrictionArtificialNode(vS_global_id, label=f"Global_vS_Res{self.restrictions.index(restriction_item)}")
            
            max_node_id_val += 1
            vD_global_id = max_node_id_val
            vD_global_node = self.RestrictionArtificialNode(vD_global_id, label=f"Global_vD_Res{self.restrictions.index(restriction_item)}")
            
            print(f"[DEBUG] Restriction {idx + 1}: Created global nodes vS={vS_global_id}, vD={vD_global_id}")
            
            # Track virtual flow demands for these nodes
            self._virtual_node_demands[vS_global_id] = virtual_flow_needed
            self._virtual_node_demands[vD_global_id] = -virtual_flow_needed
            print(f"[DEBUG] Restriction {idx + 1}: Virtual demands - vS({vS_global_id})={virtual_flow_needed}, vD({vD_global_id})={-virtual_flow_needed}")
            
            # Thêm và theo dõi các nút ảo toàn cục
            self._all_additional_nodes.update([vS_global_id, vD_global_id])
            self._graph_processor.check_and_add_nodes([vS_global_id, vD_global_id], is_artificial_node=True, label="GlobalRestrictionNode")
            self._graph_processor.ts_nodes.extend([vS_global_node, vD_global_node])
            self._graph_processor.map_nodes.update({vS_global_id: vS_global_node, vD_global_id: vD_global_node})
            print(f"[DEBUG] Restriction {idx + 1}: Added global nodes to graph")
            
            for edge_idx, edge_orig in enumerate(omega_for_this_restriction):
                u, v, l_orig, cap_orig, cost_orig = edge_orig
                print(f"[DEBUG] Restriction {idx + 1}: Processing omega edge {edge_idx + 1}: ({u}, {v}, {l_orig}, {cap_orig}, {cost_orig})")

                # Tạo các nút ảo trung gian
                max_node_id_val += 1; v_i1_id = max_node_id_val
                max_node_id_val += 1; v_i2_id = max_node_id_val
                v_i1_node = self.RestrictionArtificialNode(v_i1_id, label=f"v_i1_{u}_{v}")
                v_i2_node = self.RestrictionArtificialNode(v_i2_id, label=f"v_i2_{u}_{v}")
                
                print(f"[DEBUG] Restriction {idx + 1}: Created intermediate nodes v_i1={v_i1_id}, v_i2={v_i2_id}")
                
                # Thêm và theo dõi các nút ảo trung gian
                self._all_additional_nodes.update([v_i1_id, v_i2_id])
                self._graph_processor.check_and_add_nodes([v_i1_id, v_i2_id], is_artificial_node=True, label="IntermediateRestrictionNode")
                self._graph_processor.ts_nodes.extend([v_i1_node, v_i2_node])
                self._graph_processor.map_nodes.update({v_i1_id: v_i1_node, v_i2_id: v_i2_node})

                # Tạo và theo dõi các cung mới (chỉ các cung ảo, KHÔNG bao gồm cung gốc)
                new_edges_for_this_arc = [
                    (u, v_i1_id, l_orig, cap_orig, cost_orig),
                    (v_i1_id, v_i2_id, l_orig, cap_orig, 0),
                    (v_i2_id, v, l_orig, cap_orig, 0),
                    (vS_global_id, v_i1_id, 0, cap_orig, 0),
                    (v_i2_id, vD_global_id, 0, cap_orig, 0)
                ]
                self._all_additional_edges.extend(new_edges_for_this_arc)
                
                print(f"[DEBUG] Restriction {idx + 1}: Added {len(new_edges_for_this_arc)} new edges for omega edge {edge_idx + 1}:")
                for new_edge in new_edges_for_this_arc:
                    print(f"[DEBUG]   New edge: ({new_edge[0]}, {new_edge[1]}, {new_edge[2]}, {new_edge[3]}, {new_edge[4]})")
                
            # Tạo và theo dõi cung thoát
            escape_edge = (vS_global_id, vD_global_id, 0, virtual_flow_needed, final_gamma)
            print(f"[DEBUG] Restriction {idx + 1}: Creating escape edge: ({vS_global_id}, {vD_global_id}, 0, {virtual_flow_needed}, {final_gamma})")
            print(f"[Restriction] Adding escape edge: ({vS_global_id}, {vD_global_id}, 0, {virtual_flow_needed}, {final_gamma})")
            self._all_additional_edges.append(escape_edge)
            
            processed_restrictions += 1
            print(f"[DEBUG] Restriction {idx + 1}: Processing completed")
            
        print(f"[DEBUG] Total restrictions processed: {processed_restrictions}")
        print(f"[DEBUG] Total additional nodes created: {len(self._all_additional_nodes)}")
        print(f"[DEBUG] Total additional edges created: {len(self._all_additional_edges)}")
        print(f"[DEBUG] Additional nodes: {sorted(self._all_additional_nodes)}")
        print(f"[DEBUG] Virtual node demands: {self._virtual_node_demands}")
        
        # Sau khi xử lý tất cả, cập nhật đồ thị một lần duy nhất
        if self._all_additional_edges:
            edges_to_remove_tuples = { (int(e[0]), int(e[1])) for e in self._omega }
            original_edge_count = len(self._graph_processor.ts_edges)
            print(f"[DEBUG] Original graph has {original_edge_count} edges")
            print(f"[DEBUG] Will remove {len(edges_to_remove_tuples)} original edges: {edges_to_remove_tuples}")
            
            # Remove from both ts_edges (tuples) and tsedges (Edge objects)
            self._graph_processor.ts_edges = [e for e in self._graph_processor.ts_edges if (int(e[0]), int(e[1])) not in edges_to_remove_tuples]
            
            # Also remove from tsedges (Edge objects)
            if hasattr(self._graph_processor, 'tsedges'):
                self._graph_processor.tsedges = [
                    edge_obj for edge_obj in self._graph_processor.tsedges 
                    if edge_obj is not None and (int(edge_obj.start_node.id), int(edge_obj.end_node.id)) not in edges_to_remove_tuples
                ]
            
            removed_edges = original_edge_count - len(self._graph_processor.ts_edges)
            print(f"[DEBUG] Removed {removed_edges} original edges, graph now has {len(self._graph_processor.ts_edges)} edges")
            
            self._graph_processor.ts_edges.extend(self.get_all_additional_edges())
            self._graph_processor.create_set_of_edges(self.get_all_additional_edges())
            print(f"[DEBUG] Added {len(self.get_all_additional_edges())} additional edges, graph now has {len(self._graph_processor.ts_edges)} edges:")
            
            # Debug: Print some escape edges
            for additional_edge in self._all_additional_edges:
                print(f"[DEBUG]   Additional edge: ({additional_edge[0]}, {additional_edge[1]}, {additional_edge[2]}, {additional_edge[3]}, {additional_edge[4]})")

        print("[Restriction] Applied successfully")
        
    def generate_restriction_edges(self, start_node, end_node, nodes, adj_edges):
        pass

    def update_gamma_dynamically(self, current_time: int):
        if self.gamma_integrator is None:
            self.gamma_integrator = GammaControlIntegrator()

        # Collect current escape edges and violations for gamma adjustment
        current_escape_edges = []
        current_violations = []

        for restriction_item in self.restrictions:
            restriction_edges_config, start_time_frame, end_time_frame, U, priority, gamma_config, k_val = self.restriction_parser(restriction_item)
            
            omega_for_this_restriction = self.identify_restricted_edges(restriction_edges_config, start_time_frame, end_time_frame)
            if not omega_for_this_restriction:
                continue
            
            # Calculate current flow and virtual flow needed
            incoming_capacity = self.calculate_incoming_capacity_for_restricted_nodes(self._graph_processor.ts_edges, omega_for_this_restriction)
            outgoing_capacity = self.calculate_outgoing_capacity_for_restricted_nodes(self._graph_processor.ts_edges, omega_for_this_restriction)
            flow_F_through_omega = self.calculate_max_flow(omega_for_this_restriction, incoming_capacity, outgoing_capacity)
            virtual_flow_needed = self.calculate_virtual_flow(flow_F_through_omega, U)

            # Determine if there are violations
            violation_occurred = virtual_flow_needed > 0

            # Update gamma using the integrator
            for edge in omega_for_this_restriction:
                u, v, l_orig, cap_orig, cost_orig = edge
                if violation_occurred:
                    print(f"[Gamma Integrator] Tracking escape edge ({u}, {v})")

        # Apply the updated escape edges to the graph
        if current_escape_edges:
            for edge in current_escape_edges:
                u, v, l, cap, cost = edge
                self._all_additional_edges.append((u, v, l, cap, cost))

        # Log the current violations and escape edges for debugging
        print(f"[Gamma Update] Time: {current_time}, Violations: {len(current_violations)}, Escape edges: {len(current_escape_edges)}")
        if current_violations:
            for i, violation in enumerate(current_violations):
                print(f"  Violation {i+1}: {violation}")
        if current_escape_edges:
            for i, edge in enumerate(current_escape_edges):
                print(f"  Escape edge {i+1}: {edge}")
    
    def enable_gamma_control(self):
        """Enable gamma control integration."""
        if self.gamma_integrator is None:
            self.gamma_integrator = GammaControlIntegrator(self)
            print("[Gamma Control] Integration enabled")
        return self.gamma_integrator
    
    def set_gamma_value(self, gamma_value: float):
        """
        Set the gamma value for penalty cost calculation.
        
        Args:
            gamma_value: The gamma penalty factor to use
        """
        self._min_gamma = gamma_value
        print(f"[Gamma Control] Gamma value set to: {gamma_value}")
        
        # Update gamma integrator if it exists
        if self.gamma_integrator:
            self.gamma_integrator.set_gamma_value(gamma_value)
        
        # Update all existing restrictions to use the new gamma value
        for i, restriction in enumerate(self.restrictions):
            # Unpack the restriction tuple
            time_frames, restricted_edges, U, priority, gamma_config, k_val = restriction
            
            # Update the gamma value in the restriction
            updated_restriction = (time_frames, restricted_edges, U, priority, gamma_value, k_val)
            self.restrictions[i] = updated_restriction
            
        print(f"[Gamma Control] Updated {len(self.restrictions)} restrictions with new gamma value")

    def get_gamma_value(self) -> float:
        """
        Get the current gamma value.
        
        Returns:
            Current gamma penalty factor
        """
        return self._min_gamma

    def analyze_current_violations(self, tsg_file="TSG.txt"):
        """
        Analyze violations in the current TSG file using escape edge flow analysis.
        This should be called after apply_restriction() and TSG generation.
        """
        if self.gamma_integrator is None:
            self.enable_gamma_control()
        
        print(f"[Violation Analysis] Analyzing {tsg_file}")
        
        # Detect escape edges in current TSG
        escape_edges = self.gamma_integrator.detect_escape_edges(tsg_file)
        self.last_escape_edges = escape_edges
        
        if not escape_edges:
            print("[Violation Analysis] ERROR: No escape edges found")
            return []
        
        print(f"[Violation Analysis] Found {len(escape_edges)} escape edges")
        
        # Analyze flow through escape edges
        violations = self.gamma_integrator.analyze_escape_edge_flow(escape_edges, tsg_file)
        self.last_violations = violations
        
        if violations:
            print(f"[Violation Analysis] {len(violations)} violations detected:")
            for i, violation in enumerate(violations):
                print(f"  Violation {i+1}: {violation}")
        else:
            print("[Violation Analysis] No violations found - all restrictions satisfied")
        return violations
    
    def test_gamma_impact(self, gamma_values: List[float], simulation_runner):
        """
        Test the impact of different gamma values on violations.
        
        Args:
            gamma_values: List of gamma values to test
            simulation_runner: Function that runs the full simulation pipeline
        """
        if self.gamma_integrator is None:
            self.enable_gamma_control()
        
        print(f"[Gamma Testing] Testing {len(gamma_values)} gamma values: {gamma_values}")
        
        return self.gamma_integrator.test_gamma_values(gamma_values, simulation_runner)
    
    def get_violation_summary(self):
        """Get summary of last analyzed violations."""
        summary = {
            'escape_edges_count': len(self.last_escape_edges),
            'violations_count': len(self.last_violations),
            'total_violation_flow': sum(v['flow'] for v in self.last_violations),
            'total_penalty_cost': sum(v['penalty_cost'] for v in self.last_violations),
            'violated_edges': [(v['source'], v['dest']) for v in self.last_violations]
        }
        
        print(f"[Violation Summary] Escape edges: {summary['escape_edges_count']}, Violations: {summary['violations_count']}, Flow: {summary['total_violation_flow']}, Cost: {summary['total_penalty_cost']}")
        if summary['violated_edges']:
            print(f"  Violated edges: {summary['violated_edges']}")
        
        return summary
    
    # --- OMEGA ACCESS METHODS ---
    def get_omega(self) -> List[List[Tuple[int, int, int, int, int]]]:
        """
        Get the omega data structure containing restricted edges.
        Returns a list of weakly connected subgraphs from the omega edges.
        """
        if not self._omega:
            return []
        
        # Extract weakly connected subgraphs from omega
        subgraphs = self.extract_weakly_connected_subgraph(self._omega)
        return subgraphs
    
    def set_omega(self, omega: List[Tuple[int, int, int, int, int]]) -> None:
        """Set the omega data structure"""
        self._omega = omega

    def _print_restriction_info(self, idx: int, restriction_item: tuple) -> None:
        """Print restriction information in a formatted way."""
        restriction_edges_config, start_time_frame, end_time_frame, U, priority, gamma_config, k_val = self.restriction_parser(restriction_item)
        
        print(f"[Restriction #{idx + 1}] Timeframe: [{start_time_frame}, {end_time_frame}], Max AGVs: {U}, Priority: {priority}, Gamma: {gamma_config if gamma_config else 'AUTO'}, K: {k_val}, Edges: {len(restriction_edges_config)}")

    def print_all_restrictions(self) -> None:
        """Print all current restrictions in a formatted way."""
        if not self.restrictions:
            print("[Restrictions] No restrictions currently defined")
            return
        
        print(f"[Restrictions Overview] Total: {len(self.restrictions)}")
        
        for idx, restriction_item in enumerate(self.restrictions):
            self._print_restriction_info(idx, restriction_item)
    
    def get_virtual_node_demands(self) -> Dict[int, int]:
        """
        Get mapping of virtual node IDs to their demand values.
        Returns: Dict where key is node_id and value is demand (positive for source, negative for sink)
        """
        return self._virtual_node_demands.copy()
    
    def get_virtual_node_demand(self, node_id: int) -> int:
        """
        Get demand value for a specific virtual node.
        Returns: demand value, or 0 if node is not a virtual restriction node
        """
        return self._virtual_node_demands.get(node_id, 0)