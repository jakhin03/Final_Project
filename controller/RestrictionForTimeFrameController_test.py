from controller.NodeGenerator import ArtificialNode
from model.Edge import ArtificialEdge
from collections import defaultdict
from model.Graph import Graph
from typing import List, Tuple, Set, Optional, Dict
import networkx as nx

class RestrictionForTimeFrameController:
    def __init__(self, graph_processor):
        # Store all restrictions
        self.restrictions = []
        # Get values from graph processor
        self.M = graph_processor.M
        self.H = graph_processor.H
        self.graph_processor = graph_processor
        self.ts_nodes = graph_processor.ts_nodes
        self.ts_edges = graph_processor.ts_edges
        self.map_nodes = graph_processor.map_nodes

    class RestrictionArtificialNode(ArtificialNode):
        def __init__(self, id: int, label: Optional[str] = None):
            super().__init__(id, label)
            self.is_restriction_node = True
            self.is_artificial = True
        def __repr__(self):
            return f"RestrictedArtificialNode(id={self.id}, label='{self.label}', temporary={self.temporary})"

    def validate_restriction(self, restriction_edges: List[List[int]], timeframe: List[int], U: int, penalty: int) -> bool:
        # Check if restriction is ok
        if not restriction_edges or not timeframe or U < 0 or penalty < 0:
            print("Restriction không hợp lệ")
            return False
        if len(timeframe) != 2 or timeframe[0] > timeframe[1]:
            print("Time frame không hợp lệ")
            return False
        if not all(len(edge) == 2 for edge in restriction_edges):
            print("Restriction edges format không hợp lệ")
            return False
        return True

    def get_restrictions(self) -> bool:
        """Get restrictions from user input with validation."""
        try:
            L = int(input("Nhập số restrictions: "))
            if L < 0:
                print("Số restrictions phải lớn hơn hoặc bằng 0")
                return False
            for i in range(L):
                timeframe = list(map(int, input(f"Nhập timeframe cho restriction thứ {i+1} (vd: 3 4): ").split()))
                restriction_nodes = list(map(int, input(f"    Nhập các edges cho timeframe {timeframe} (vd 3 4 5 6 là 2 edge [3,4] và [5,6]): ").split()))
                try:
                    U = int(input(f"    Nhập số lượng AGV tối đa (U) cho restriction {i+1}: "))
                    penalty = int(input(f"    Nhập chi phí phạt (penalty) cho restriction {i+1}: "))
                except ValueError:
                    print("U hoặc penalty không hợp lệ")
                    continue
                if len(restriction_nodes) % 2 != 0 or len(restriction_nodes) < 2:
                    print("Restriction edge không hợp lệ")
                    continue
                restriction_edges = [[restriction_nodes[j], restriction_nodes[j+1]] for j in range(0, len(restriction_nodes), 2)]
                if self.validate_restriction(restriction_edges, timeframe, U, penalty):
                    self.restrictions.append((restriction_edges, timeframe, U, penalty))
            return bool(self.restrictions)
        except ValueError as e:
            print(f"Input error: {str(e)}")
            return False

    def set_restrictions(self, restrictions_data: List[Tuple[List[List[int]], List[int], int, int]]) -> bool:
        # Put restrictions into our list
        self.restrictions = []
        for restriction_edges, timeframe, U, penalty in restrictions_data:
            if self.validate_restriction(restriction_edges, timeframe, U, penalty):
                self.restrictions.append((restriction_edges, timeframe, U, penalty))
        return len(self.restrictions) > 0

    def restriction_parser(self, restriction: Tuple[List[List[int]], List[int], int, int]) -> Tuple[List[List[int]], int, int, int, int]:
        # Break down a single restriction into its parts
        restriction_edges, [start_time_frame, end_time_frame], U, penalty = restriction
        return restriction_edges, start_time_frame, end_time_frame, U, penalty

    def _get_node_time(self, node_id: int) -> int:
        return node_id // self.M - (1 if node_id % self.M == 0 else 0)

    def _get_node_coordinates(self, node_id: int) -> int:
        # Get the space position of a node
        return node_id % self.M if node_id % self.M != 0 else self.M

    def compute_max_flow(self, restriction_idx: int) -> int:
        # Find max flow F through Omega using max-cost flow
        restriction = self.restrictions[restriction_idx]
        restriction_edges, start_time, end_time, U, gamma = self.restriction_parser(restriction)
        restriction_set = {(u, v) for u, v in restriction_edges}

        # Make Omega subgraph
        G_omega = nx.DiGraph()
        for edge in self.ts_edges:
            source_id, dest_id, lower, capacity, cost = edge
            t1 = self._get_node_time(source_id)
            s_source = self._get_node_coordinates(source_id)
            s_dest = self._get_node_coordinates(dest_id)
            base_edge = (s_source, s_dest)
            
            # Add edge with cost 2 if in restriction
            if base_edge in restriction_set and start_time <= t1 <= end_time:
                G_omega.add_edge(source_id, dest_id, capacity=capacity, cost=2)
            else:
                G_omega.add_edge(source_id, dest_id, capacity=capacity, cost=0)

        # Add start and end nodes
        vS_prime = 'source_prime'
        vD_prime = 'sink_prime'
        G_omega.add_node(vS_prime)
        G_omega.add_node(vD_prime)

        # Link vS_prime to AGV start nodes and vD_prime to end nodes
        for node_id in G_omega.nodes:
            if self._get_node_time(node_id) == 0:  # AGVs start at t=0
                G_omega.add_edge(vS_prime, node_id, capacity=1, cost=0)
            if self._get_node_time(node_id) == self.H - 1:  # End at max time
                G_omega.add_edge(node_id, vD_prime, capacity=1, cost=0)

        # Add escape edge
        initial_F = sum(data['capacity'] for u, v, data in G_omega.edges(data=True) if data['cost'] == 2)
        G_omega.add_edge(vS_prime, vD_prime, capacity=initial_F, cost=1)

        # Solve max-cost flow
        flow_dict = nx.max_flow_min_cost(G_omega, vS_prime, vD_prime, capacity='capacity', weight='cost')
        
        # Get flow through escape edge
        E = 0
        if vD_prime in flow_dict[vS_prime]:
            E = flow_dict[vS_prime][vD_prime]
            
        # Calculate final flow
        F = self.M - E
        if F > self.M:
            F = self.M
        return F

    def identify_restricted_edges(self, restriction_edges: List[List[int]], start_time_frame: int, end_time_frame: int) -> Tuple[List[Tuple[int, int]], Set[int]]:
        """Identify edges in Omega and Omega(Out) nodes."""
        S_TSG = []
        restriction_set = {(u, v) for u, v in restriction_edges}
        G = nx.DiGraph()
        for edge in self.ts_edges:
            source_id, dest_id, lower, capacity, cost = edge
            G.add_edge(source_id, dest_id, capacity=capacity, cost=cost)

        # Identify Omega edges
        for edge in self.ts_edges:
            source_id, dest_id, _, capacity, cost = edge
            t1 = self._get_node_time(source_id)
            s_source = self._get_node_coordinates(source_id)
            s_dest = self._get_node_coordinates(dest_id)
            base_edge = (s_source, s_dest)
            if base_edge in restriction_set and start_time_frame <= t1 <= end_time_frame:
                S_TSG.append((source_id, dest_id))

        # Identify Omega(Out) nodes
        omega_out = set()
        for u, v in S_TSG:
            for _, w in G.out_edges(v):
                t2 = self._get_node_time(w)
                s_v = self._get_node_coordinates(v)
                s_w = self._get_node_coordinates(w)
                base_edge = (s_v, s_w)
                if base_edge not in restriction_set or t2 < start_time_frame or t2 > end_time_frame:
                    omega_out.add(v)

        return S_TSG, omega_out

    def apply_restriction(self) -> None:
        """Apply all restrictions to the graph using the new algorithm."""
        if not self.get_restrictions():
            return

        for idx, restriction in enumerate(self.restrictions):
            restriction_edges, start_time_frame, end_time_frame, U, penalty = self.restriction_parser(restriction)
            S_TSG, omega_out = self.identify_restricted_edges(restriction_edges, start_time_frame, end_time_frame)

            if not S_TSG:
                print(f"Không tìm thấy cung nào trong restriction {restriction}")
                continue

            # Compute max flow F
            F = self.compute_max_flow(idx)
            if F <= U:
                print(f"Đã thoả mãn restriction {restriction}")
                continue

            # Create virtual nodes
            max_id = self.graph_processor.get_max_id() + 1
            vS = self.RestrictionArtificialNode(max_id, label='vS')
            vD = self.RestrictionArtificialNode(max_id + 1, label='vD')
            self.ts_nodes.extend([vS, vD])
            self.map_nodes.update({vS.id: vS, vD.id: vD})
            self.graph_processor.check_and_add_nodes([vS.id, vD.id], is_artificial_node=True, label="Restriction")
            next_node_id = max_id + 2

            # Create new edges
            new_edges = []
            for edge in self.ts_edges:
                source_id, dest_id, lower, capacity, cost = edge
                if (source_id, dest_id) in S_TSG and dest_id in omega_out:
                    # Insert artificial nodes v1, v2
                    v1 = self.RestrictionArtificialNode(next_node_id, label=f'v_{next_node_id}')
                    v2 = self.RestrictionArtificialNode(next_node_id + 1, label=f'v_{next_node_id + 1}')
                    self.ts_nodes.extend([v1, v2])
                    self.map_nodes.update({v1.id: v1, v2.id: v2})
                    self.graph_processor.check_and_add_nodes([v1.id, v2.id], is_artificial_node=True, label="Restriction")
                    next_node_id += 2

                    # Add edges: (u, v1), (v1, v2), (v2, v)
                    new_edges.append((source_id, v1.id, lower, capacity, cost))
                    new_edges.append((v1.id, v2.id, lower, capacity, 0))
                    new_edges.append((v2.id, dest_id, lower, capacity, 0))
                    # Connect to vS and vD
                    new_edges.append((vS.id, v1.id, 0, capacity, 0))
                    new_edges.append((v2.id, vD.id, 0, capacity, 0))
                else:
                    new_edges.append(edge)

            # Add escape edge (vS, vD)
            new_edges.append((vS.id, vD.id, F - U, F - U, penalty))

            # Update ts_edges
            self.ts_edges = new_edges
            self.graph_processor.ts_edges = new_edges
            self.graph_processor.create_set_of_edges(set(new_edges))

        self.graph_processor.insert_halting_edges()
        self.graph_processor.write_to_file()
        print("Đã áp dụng tất cả restrictions thành công")
        
        # TODO: Cần xử lý 
        # print("Kiểm tra lại vi phạm restrictions")
        # self.check_paths_compliance(self.find_paths_using_network_simplex())

    def find_paths_using_network_simplex(self) -> List[List[int]]:
        # Find paths for all AGVs using Network Simplex after adding restrictions
        from model.NXSolution import NetworkXSolution
        import networkx as nx

        # Make solution object
        nx_solution = NetworkXSolution()
        nx_solution.read_dimac_file('TSG_true.txt')
        G = nx_solution.G
        
        # Get flow
        nx_solution.flowCost, nx_solution.flowDict = nx.network_simplex(G)

        # Keep only positive flows in flow dictionary
        filtered_data = {}
        for key, sub_dict in nx_solution.flowDict.items():
            filtered_sub_dict = {k: v for k, v in sub_dict.items() if v != 0}
            if filtered_sub_dict:
                filtered_data[key] = filtered_sub_dict
        nx_solution.flowDict = filtered_data

        # Get paths from flow dictionary
        paths = []
        for source, flows in nx_solution.flowDict.items():
            for target, flow in flows.items():
                if flow > 0:
                    path = self._find_path_in_flow_dict(nx_solution.flowDict, source, target)
                    if path:
                        path = [int(node_id) for node_id in path]
                        paths.append(path)
        return paths

    def _find_path_in_flow_dict(self, flow_dict: Dict, source: str, target: str) -> List[str]:
        # Find path from start to end
        path = [source]
        current = source
        while current != target:
            next_node = None
            for node, flow in flow_dict.get(current, {}).items():
                if flow > 0:
                    next_node = node
                    break
            if next_node is None:
                return []
            # Add next node to path
            path.append(next_node)
            current = next_node
        return path

    def print_violations(self, violations: Dict) -> None:
        """Print violations in a formatted way."""
        if not violations:
            print("Tất cả AGV đã tuân thủ restrictions")
            return
        print("\nĐã phát hiện vi phạm restriction:")
        for restriction_idx, violation_list in violations.items():
            restriction = self.restrictions[restriction_idx]
            print(f"Restriction {restriction_idx + 1}: {restriction}")
            for violation in violation_list:
                if violation["type"] == "exceed_U":
                    print(f"    Vi phạm: Số AGV ({violation['agv_count']}) vượt quá U ({violation['U']})")
                    for path_violation in violation["violated_paths"]:
                        print(f"        Path {path_violation['path_idx']}: "
                              f"edge ({path_violation['edge'][0]}, {path_violation['edge'][1]}) "
                              f"tại t={path_violation['time']}, space_edge {path_violation['space_edge']}")

    def check_paths_compliance(self, paths: List[List[int]]) -> Tuple[bool, Dict]:
        # Check if paths are ok
        if not self.restrictions:
            print("Không có restrictions để kiểm tra")
            return True, {}
            
        violations = defaultdict(list)
        compliance = True
        
        # Clean up TSG file
        try:
            with open('TSG.txt', 'r') as file:
                lines = file.readlines()
            with open('TSG.txt', 'w') as file:
                for line in lines:
                    if not line.startswith('c Edge') or 'is violation' not in line:
                        file.write(line)
        except FileNotFoundError:
            pass
            
        # Check each restriction
        for restriction_idx, restriction in enumerate(self.restrictions):
            restriction_edges, [start_time_frame, end_time_frame], U, _ = restriction
            restricted_set = {(u, v) for u, v in restriction_edges}
            agv_count = 0
            path_violations = []
            
            # Check each path
            for path_idx, path in enumerate(paths):
                if not path or len(path) < 2:
                    continue
                    
                # Check each edge in path
                for i in range(len(path) - 1):
                    src_id, dest_id = path[i], path[i + 1]
                    t1 = self._get_node_time(src_id)
                    base_edge = (self._get_node_coordinates(src_id), self._get_node_coordinates(dest_id))
                    
                    # If edge is restricted
                    if base_edge in restricted_set and start_time_frame <= t1 <= end_time_frame:
                        agv_count += 1
                        # Add violation
                        path_violations.append({
                            "path_idx": path_idx,
                            "edge": (src_id, dest_id),
                            "time": t1,
                            "space_edge": base_edge
                        })
                        # Write to file
                        with open('TSG.txt', 'a') as file:
                            file.write(f"c Edge {src_id} {dest_id} is violation\n")
                            
            # Check if too many AGVs
            if agv_count > U:
                violations[restriction_idx].append({
                    "type": "exceed_U",
                    "agv_count": agv_count,
                    "U": U,
                    "violated_paths": path_violations
                })
                compliance = False
                
        self.print_violations(violations)
        return compliance, violations