from controller.NodeGenerator import ArtificialNode
from collections import defaultdict
from model.Graph import Graph
from typing import List, Tuple, Set, Optional, Dict
import numpy as np
import networkx as nx
import config
from controller.RestrictionController import RestrictionController

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
        additional_nodes_ids = self.get_all_additional_nodes()
        additional_edges_tuples = self.get_all_additional_edges()

        # Xóa các nút ảo
        if additional_nodes_ids:
            self.graph_processor.ts_nodes = [
                node for node in self.graph_processor.ts_nodes
                if node.id not in additional_nodes_ids
            ]
            for node_id in additional_nodes_ids:
                self.graph_processor.map_nodes.pop(node_id, None)

        # Xóa các cung ảo
        if additional_edges_tuples:
            # Tạo một set từ tuple của các cung ảo để tìm kiếm nhanh hơn
            additional_edges_set = { (e[0], e[1]) for e in additional_edges_tuples }
            
            # Xóa từ self.graph_processor.ts_edges (list of tuples)
            self.graph_processor.ts_edges = [
                edge for edge in self.graph_processor.ts_edges
                if (edge[0], edge[1]) not in additional_edges_set
            ]
            # Xóa từ self.graph_processor.tsedges (list of Edge objects)
            if hasattr(self.graph_processor, 'tsedges'):
                 self.graph_processor.tsedges = [
                    edge_obj for edge_obj in self.graph_processor.tsedges
                    if hasattr(edge_obj, 'start_node') and (edge_obj.start_node.id, edge_obj.end_node.id) not in additional_edges_set
                ]

        # Khôi phục các cung gốc đã bị xóa
        original_edges_to_re_add = {
            edge for edge in self._omega
            if any((e[0], e[1]) in additional_edges_set for e in self.get_all_additional_edges()) # Heuristic to find which omega was processed
        }
        if original_edges_to_re_add:
            self.graph_processor.ts_edges.extend(list(original_edges_to_re_add))
            self.graph_processor.create_set_of_edges(original_edges_to_re_add)

        # Reset lại trạng thái
        self.set_all_additional_nodes(set())
        self.set_all_additional_edges([])
        self._omega = []
        print("Đã dọn dẹp và khôi phục lại các thực thể ảo.")


    
    class RestrictionArtificialNode(ArtificialNode):
        def __init__(self, id: int, label: Optional[str] = None):
            super().__init__(id, label)
            self.is_restriction_node = True
        def __repr__(self):
            return f"RestrictedArtificialNode(id={self.id}, label='{self.label}', temporary={self.temporary})"

    def validate_restriction(self, restriction_edges: List[List[int]], timeframe: List[int], U: int) -> bool:
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

    def calculate_default_gamma(self, TSG, priority=1.0, k=1, min_gamma=200):
        if not TSG:
            return min_gamma
        costs = [cost for (_, _, _, _, cost) in TSG if cost is not None]
        avg_cost = np.mean(costs) if costs else 10
        gamma = k * avg_cost * max(1.0, priority)
        return max(gamma, min_gamma)

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

        self.restrictions = []
        try:
            L_str = input("Nhập số restrictions (để trống nếu không có): ")
            if not L_str.strip():
                self._save_restrictions_to_config()
                return False

            L = int(L_str)
            if L == 0:
                self._save_restrictions_to_config()
                return False

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
        except (ValueError, Exception) as e:
            print(f"Lỗi nhập liệu hoặc lỗi không mong muốn: {e}")
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

    def identify_restricted_edges(self, restriction_edges, start_time_frame, end_time_frame):
        omega = []
        restriction_set = {(u, v) for u, v in restriction_edges}
        for edge_tuple in self.graph_processor.ts_edges:
            source_id, dest_id, _, capacity, cost = edge_tuple
            t1 = self._get_node_time(source_id)
            t2 = self._get_node_time(dest_id)
            s_source = self._get_node_coordinates(source_id)
            s_dest = self._get_node_coordinates(dest_id)
            base_edge = (s_source, s_dest)

            if base_edge in restriction_set:
                time_intersects = (t1 < end_time_frame) and (t2 > start_time_frame)
                if time_intersects:
                    omega.append((source_id, dest_id, 0, capacity, cost))
        return omega
    
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
    
    def calculate_virtual_flow(self, max_flow, U): #...

    def apply_restriction(self) -> None:
        if not self.get_restrictions():
            return
        
        # Reset lại trạng thái nếu hàm được gọi lại
        if self._all_additional_nodes or self._all_additional_edges:
            self.remove_artificial_artifact()

        max_node_id_val = self.graph_processor.get_max_id()

        for restriction_item in self.restrictions:
            restriction_edges_config, start_time_frame, end_time_frame, U, priority, gamma_config, k_val = self.restriction_parser(restriction_item)
            
            omega_for_this_restriction = self.identify_restricted_edges(restriction_edges_config, start_time_frame, end_time_frame)
            if not omega_for_this_restriction:
                continue
            
            # Lưu lại omega để có thể khôi phục cung gốc khi dọn dẹp
            self._omega.extend(omega_for_this_restriction)

            current_restricted_nodes_set = self.identify_restricted_nodes(omega_for_this_restriction)
            incoming_capacity = self.calculate_incoming_capacity_for_restricted_nodes(self.graph_processor.ts_edges, current_restricted_nodes_set)
            outgoing_capacity = self.calculate_outgoing_capacity_for_restricted_nodes(self.graph_processor.ts_edges, current_restricted_nodes_set)
            
            flow_F_through_omega = self.calculate_max_flow(omega_for_this_restriction, incoming_capacity, outgoing_capacity)
            virtual_flow_needed = self.calculate_virtual_flow(flow_F_through_omega, U)

            if virtual_flow_needed <= 0:
                continue

            final_gamma = int(round(gamma_config if gamma_config is not None else self.calculate_default_gamma(self.graph_processor.ts_edges, priority, k_val, self._min_gamma)))
            
            # Tạo nút ảo toàn cục cho ràng buộc này
            max_node_id_val += 1
            vS_global_id = max_node_id_val
            vS_global_node = self.RestrictionArtificialNode(vS_global_id, label=f"Global_vS_Res{self.restrictions.index(restriction_item)}")
            
            max_node_id_val += 1
            vD_global_id = max_node_id_val
            vD_global_node = self.RestrictionArtificialNode(vD_global_id, label=f"Global_vD_Res{self.restrictions.index(restriction_item)}")
            
            # Thêm và theo dõi các nút ảo toàn cục
            self._all_additional_nodes.update([vS_global_id, vD_global_id])
            self.graph_processor.check_and_add_nodes([vS_global_id, vD_global_id], is_artificial_node=True, label="GlobalRestrictionNode")
            self.graph_processor.ts_nodes.extend([vS_global_node, vD_global_node])
            self.graph_processor.map_nodes.update({vS_global_id: vS_global_node, vD_global_id: vD_global_node})

            for edge_orig in omega_for_this_restriction:
                u, v, l_orig, cap_orig, cost_orig = edge_orig
                self._all_additional_edges.append(edge_orig) # Theo dõi cung gốc để xóa

                # Tạo các nút ảo trung gian
                max_node_id_val += 1; v_i1_id = max_node_id_val
                max_node_id_val += 1; v_i2_id = max_node_id_val
                v_i1_node = self.RestrictionArtificialNode(v_i1_id, label=f"v_i1_{u}_{v}")
                v_i2_node = self.RestrictionArtificialNode(v_i2_id, label=f"v_i2_{u}_{v}")
                
                # Thêm và theo dõi các nút ảo trung gian
                self._all_additional_nodes.update([v_i1_id, v_i2_id])
                self.graph_processor.check_and_add_nodes([v_i1_id, v_i2_id], is_artificial_node=True, label="IntermediateRestrictionNode")
                self.graph_processor.ts_nodes.extend([v_i1_node, v_i2_node])
                self.graph_processor.map_nodes.update({v_i1_id: v_i1_node, v_i2_id: v_i2_node})

                # Tạo và theo dõi các cung mới
                new_edges_for_this_arc = [
                    (u, v_i1_id, l_orig, cap_orig, cost_orig),
                    (v_i1_id, v_i2_id, l_orig, cap_orig, 0),
                    (v_i2_id, v, l_orig, cap_orig, 0),
                    (vS_global_id, v_i1_id, 0, cap_orig, 0),
                    (v_i2_id, vD_global_id, 0, cap_orig, 0)
                ]
                self._all_additional_edges.extend(new_edges_for_this_arc)
                
            # Tạo và theo dõi cung thoát
            escape_edge = (vS_global_id, vD_global_id, 0, virtual_flow_needed, final_gamma)
            self._all_additional_edges.append(escape_edge)
            
        # Sau khi xử lý tất cả, cập nhật đồ thị một lần duy nhất
        if self._all_additional_edges:
            edges_to_remove_tuples = { (e[0], e[1]) for e in self._omega }
            self.graph_processor.ts_edges = [e for e in self.graph_processor.ts_edges if (e[0], e[1]) not in edges_to_remove_tuples]
            self.graph_processor.ts_edges.extend(self.get_all_additional_edges())
            self.graph_processor.create_set_of_edges(self.get_all_additional_edges())

        print("Đã áp dụng tất cả restrictions theo thuật toán mới thành công.")
        
    def generate_restriction_edges(self, start_node, end_node, nodes, adj_edges):
        pass