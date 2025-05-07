import networkx as nx
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import simpledialog, messagebox

# Hàm vẽ đồ thị với luồng và nhãn
def draw_flow(G, flow_dict, pos, flow_value):
    edge_labels = {
        (u, v): f"{flow_dict[u][v]}/{G[u][v]['capacity']}"
        for u, v in G.edges()
        if 'capacity' in G[u][v]
    }

    edge_colors = []
    for u, v in G.edges():
        if u == 'super_source' or v == 'super_sink':
            edge_colors.append('blue')
        else:
            edge_colors.append('black')

    plt.figure(figsize=(10, 6))
    nx.draw(G, pos, with_labels=True, node_color='lightblue', node_size=2000,
            font_size=12, arrowsize=20, edge_color=edge_colors)
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color='red')
    plt.title("Luồng cực đại với nhãn (flow/capacity) - Đồ thị planar")
    plt.text(0, -0.5, f"Giá trị max flow: {flow_value}", fontsize=14, color='darkgreen')
    plt.axis('off')
    plt.tight_layout()
    plt.show()

# Tạo đồ thị có hướng
G = nx.DiGraph()

# Thêm các cạnh với capacity
edges = [
    ('A', 'C', 1),
    ('B', 'C', 1),
    ('C', 'D', 2),
    ('D', 'E', 1),
    ('D', 'F', 1)
]

for u, v, cap in edges:
    G.add_edge(u, v, capacity=cap)

# Định nghĩa vị trí cố định để giữ layout planar
pos = {
    'super_source': (-2, 1.5), 'A': (-1, 2), 'B': (-1, 0),
    'C': (0, 1), 'D': (1, 1), 'E': (2, 2), 'F': (2, 0),
    'super_sink': (3, 1)
}

# Giao diện người dùng để nhập nguồn và đích kèm capacity
root = tk.Tk()
root.withdraw()

source_input = simpledialog.askstring(
    "Nhập nguồn",
    "Nhập danh sách các nút nguồn và capacity, ví dụ: A=2,B=1,D"
)
sink_input = simpledialog.askstring(
    "Nhập đích",
    "Nhập danh sách các nút đích và capacity, ví dụ: E=2,F"
)

def parse_node_caps(raw_input):
    result = {}
    for item in raw_input.split(','):
        item = item.strip()
        if '=' in item:
            name, cap = item.split('=')
            try:
                result[name.strip()] = int(cap.strip())
            except:
                result[name.strip()] = float('inf')
        else:
            result[item] = float('inf')
    return result

source_caps = parse_node_caps(source_input)
sink_caps = parse_node_caps(sink_input)

sources = list(source_caps.keys())
sinks = list(sink_caps.keys())

# Tạo nguồn và đích ảo
G.add_node('super_source')
G.add_node('super_sink')

for source in sources:
    if source in G.nodes:
        G.add_edge('super_source', source, capacity=source_caps[source])

for sink in sinks:
    if sink in G.nodes:
        G.add_edge(sink, 'super_sink', capacity=sink_caps[sink])

# Tính max-flow và vẽ đồ thị
flow_value, flow_dict = nx.maximum_flow(G, 'super_source', 'super_sink')
messagebox.showinfo("Kết quả", f"Giá trị max flow: {flow_value}")

draw_flow(G, flow_dict, pos, flow_value)
