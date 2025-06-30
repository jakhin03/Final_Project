import networkx as nx
import pdb
import config
from collections import defaultdict
import plotly.graph_objects as go
from plotly.subplots import make_subplots


class NetworkXSolution:
    def __init__(self):#, edges_with_costs, startednodes, targetnodes):
        self.startednodes = None #startednodes
        self.targetnodes = None #targetnodes
        self.edges_with_costs = None #edges_with_costs
        self.flowCost = 0
        self.flowDict = defaultdict(list)
        self.M = config.M
    def is_artificial_edge(self, edge):
        # Check if either node in the edge is artificial
        node1, node2 = edge
        return (self.G.nodes[node1].get('is_artificial', False) or 
                self.G.nodes[node2].get('is_artificial', False))

    
    def is_restriction_violation(self, edge):
        """Check if an edge violates any restrictions by looking for violation comments in TSG file."""
        try:
            with open('TSG.txt', 'r') as file:
                for line in file:
                    if line.startswith('c Edge') and 'violates' in line:
                        parts = line.strip().split()
                        if len(parts) >= 6:
                            source = int(parts[2])
                            dest = int(parts[3])
                            n = int(parts[5])
                            if (str(edge[0]) == str(source) and str(edge[1]) == str(dest)):
                                return n 
        except FileNotFoundError:
            pass
        return False
    
    def is_escape_edge(self, edge):
        """Check if an edge is an escape edge (vS_global to vD_global) based on node labels."""
        try:
            node1, node2 = edge
            node1_label = self.G.nodes[node1].get('label', '')
            node2_label = self.G.nodes[node2].get('label', '')
            return ('Global_vS_Res' in node1_label and 'Global_vD_Res' in node2_label)
        except:
            return False
    
    def count_violation_flow(self):
        """Count the total flow through escape edges as violations."""
        total_violations = 0
        for source_node, flow_dict in self.flowDict.items():
            for dest_node, flow_value in flow_dict.items():
                if flow_value > 0 and self.is_escape_edge((source_node, dest_node)):
                    total_violations += flow_value
        return total_violations  
    
    def plot_graph_3d_interactive(self, G):
        if(config.draw == 0):
            return
        pos = nx.spring_layout(G, dim=3)
        
        my_dict = {}
        for key, value in self.flowDict.items():
            for inner_key, inner_value in value.items():
                if(inner_value > 0):
                    my_dict[(key, inner_key)] = 1
        
        # Define colors for different edge types
        edge_color_map = {
            'flow': 'green',           # Edges with flow
            'time': 'blue',        # Time edges
            # 'artificial': 'red',  # Artificial edges
            'restriction': 'yellow', # Edges that violate restrictions
            'normal': 'black'        # Normal edges
        }
        
        edge_trace = []
        for edge in G.edges():
            x0, y0, z0 = pos[edge[0]]
            x1, y1, z1 = pos[edge[1]]
            
            # Determine edge color based on its properties
            if (edge[0], edge[1]) in my_dict:
                color = edge_color_map['flow']
            elif (int(edge[1]) - int(edge[0])) == self.M:
                color = edge_color_map['time']
            # elif self.is_artificial_edge(edge):
            #     color = edge_color_map['artificial']
            elif self.is_restriction_violation(edge):
                color = edge_color_map['restriction']
            else:
                color = edge_color_map['normal']
            
            edge_trace.append(go.Scatter3d(
                x=[x0, x1, None], y=[y0, y1, None], z=[z0, z1, None],
                mode='lines',
                line=dict(color=color, width=5),
                hoverinfo='none'
            ))
        
        # Define colors for different node types
        node_color_map = {
            'normal': {
                -1: 'red',    # Demand nodes
                0: 'blue',    # Zero nodes
                1: 'green'    # Supply nodes
            },
            'artificial': 'purple'  # Artificial nodes
        }
        #node_colors = ['red' if G.nodes[node].get('demand', 0) == -1 else  else 'blue' for node in G.nodes()]
        node_colors = []
        for node in G.nodes():
            if G.nodes[node].get('is_artificial', False):
                node_colors.append(node_color_map['artificial'])
            else:
                demand = G.nodes[node].get('demand', 0)
                node_colors.append(node_color_map['normal'][demand])
        node_trace = go.Scatter3d(
            x=[pos[node][0] for node in G.nodes()],
            y=[pos[node][1] for node in G.nodes()],
            z=[pos[node][2] for node in G.nodes()],
            mode='markers+text',
            marker=dict(
                size=10,
                color=node_colors,
                line=dict(width=2)  # Add border to make nodes more visible
            ),
            text=[str(node) for node in G.nodes()],
            hoverinfo='text'
        )
        # Tạo bảng
        table_trace = go.Table(
            header=dict(values=['Edge: Lower Bound/Upper Bound/Cost']),
            cells=dict(values=[
                [f"({edge[0]}, {edge[1]}): 0/{G.edges[edge].get('capacity', 0)}/{G.edges[edge].get('weight', 0)}" for edge in G.edges()]
                ])
        )
        #fig = go.Figure(data=edge_trace + [node_trace, table_trace])
        # Tạo subplot với hai cột
        fig = make_subplots(
            rows=1, cols=2,
            column_widths=[0.2, 0.8],
            specs=[[{"type": "table"}, {"type": "scatter3d"}]]
            )
        
        fig.add_trace(table_trace, row=1, col=1)
        fig.add_trace(node_trace, row=1, col=2)
        for trace in edge_trace:
            fig.add_trace(trace, row=1, col=2)
        fig.update_layout(showlegend=False, title = 'Vẽ đồ thị cho tôi:',\
            title_text='3D Graph Visualization')
        fig.show()

    def read_dimac_file(self, file_path):
        G = nx.DiGraph()
        self.G = G  # Store G as instance variable
        artificial_nodes = set()  # Track artificial nodes
        countDemands = 0
        posList = []
        negList = []
        with open(file_path, 'r') as file:
            for line in file:
                parts = line.split()
                if parts[0] == 'c' and 'ArtificialNode' in line:
                    # Extract node ID from comment line
                    node_id = parts[2]
                    artificial_nodes.add(node_id)
                elif parts[0] == 'n':
                    ID = parts[1]
                    demand = (-1)*int(parts[2])
                    countDemands += 1
                    if demand > 0:
                        posList.append(demand)
                    else:
                        negList.append(demand)
                    G.add_node(ID, demand=demand, is_artificial=ID in artificial_nodes)
                elif parts[0] == 'a':
                    ID1 = (parts[1])
                    ID2 = (parts[2])
                    U = int(parts[4])
                    C = int(parts[5])
                    G.add_edge(ID1, ID2, weight=C, capacity=U)
        import time
        start_time = time.time()
        # Restriction 2 5 4 1 1 2
        pdb.set_trace()
        self.flowCost, self.flowDict = nx.network_simplex(G)
        end_time = time.time()
        config.timeSolving += (end_time - start_time)
        config.totalSolving += 1
        filtered_data = {}
        for key, sub_dict in self.flowDict.items():
            # Lọc các phần tử có giá trị khác 0
            filtered_sub_dict = {k: v for k, v in sub_dict.items() if v != 0}
            if filtered_sub_dict:
                filtered_data[key] = filtered_sub_dict
        self.flowDict = filtered_data
        self.plot_graph_3d_interactive(G)
        
    def write_trace(self, file_path = 'traces.txt'):
        #pdb.set_trace()

        with open(file_path, "w") as file:
            for key, value in self.flowDict.items():
                for inner_key, inner_value in value.items():
                    if(inner_value > 0):
                        s = int(key) // self.M + (self.M if int(key) // self.M == 0 else 0)
                        t = int(inner_key) // self.M + (self.M if int(inner_key) // self.M == 0 else 0)
                        cost = self.edges_with_costs.get((s, t), [-1, -1])[1]
                        result = inner_value*cost
                        #print(f"a {key} {inner_key} 0 + {result} = {result}")
                        file.write(f"a {key} {inner_key} 0 + {result} = {result}\n")
