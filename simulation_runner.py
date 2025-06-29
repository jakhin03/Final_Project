import sys
import io
import os
import re
from datetime import datetime
import importlib
import traceback
import time
import numpy as np

# --- Import các thư viện và lớp cần thiết ---
import discrevpy
from discrevpy.simulator import Simulator

# Import các module của dự án
from model.Graph import Graph
from model.AGV import AGV
from model.Event import Event
from controller.GraphProcessor import GraphProcessor
from model.Logger import Logger
from model.hallway_simulator_module.HallwaySimulator import DirectoryManager
from controller.RestrictionForTimeFrameController import RestrictionForTimeFrameController
import config as sim_config

# --- Lớp tiện ích để bắt output từ console ---
class StdoutCapture:
    def __init__(self):
        self.buffer = io.StringIO()
        self.original_stdout = None

    def __enter__(self):
        self.original_stdout = sys.stdout
        sys.stdout = self.buffer
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self.original_stdout

    def get_value(self):
        return self.buffer.getvalue()

# --- Hàm tiện ích để phân tích log ---
def parse_solution_from_log(log_text, M):
    """
    Phân tích log để lấy đường đi và chi phí.
    """
    solutions = []
    agv_paths = {}
    
    path_pattern = re.compile(r"AGV(\w+)'s path: \[(.*?)\]")
    for match in path_pattern.finditer(log_text):
        agv_id = match.group(1).replace("AGV", "")
        path_str = match.group(2)
        ts_path = [int(p.strip()) for p in path_str.split(',') if p.strip().isdigit()]
        
        # Sử dụng công thức chuyển đổi ID chính xác.
        # ID không gian = ((ID không-thời gian - 1) % M) + 1
        space_path = [((p - 1) % M) + 1 for p in ts_path if p > 0]
        agv_paths[agv_id] = space_path

    cost_pattern = re.compile(r"The total cost of AGV(\w+) is ([\d.]+)")
    for match in cost_pattern.finditer(log_text):
        agv_id = match.group(1).replace("AGV", "")
        cost = float(match.group(2))
        solutions.append({
            "agv_id": agv_id,
            "cost": cost,
            "path": agv_paths.get(agv_id, [])
        })
        
    return solutions

# --- HÀM MÔ PHỎNG CHÍNH ---
def run_simulation(api_config: dict) -> dict:
    """
    Hàm chính để chạy mô phỏng, điều phối các bước khởi tạo theo đúng thứ tự logic.
    """
    try:
        # --- BƯỚC 0: KHỞI TẠO MÔI TRƯỜNG SẠCH ---
        dm = DirectoryManager()
        dm.full_cleanup()

        # SỬA LỖI STATE: Thử reset simulator. Nếu nó ở trạng thái 'INIT' (lần đầu),
        # nó sẽ báo lỗi ValueError, chúng ta sẽ bắt và bỏ qua lỗi này một cách an toàn.
        # Đây là cách xử lý đúng đắn mà không cần truy cập vào thuộc tính nội bộ.
        try:
            discrevpy.simulator.reset()
        except ValueError as e:
            # Chỉ bỏ qua lỗi cụ thể về việc reset sai trạng thái,
            # và ném lại các lỗi ValueError không mong muốn khác.
            if "Reset can only be performed when the state is FINISHED" not in str(e):
                raise
        
        AGV.reset()

        # --- BƯỚC 1: THIẾT LẬP CẤU HÌNH TỪ API ---
        server_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        map_name = api_config.get('map_name', 'simplest.txt')
        
        sim_config.filepath = os.path.join(server_dir, 'maps', map_name)
        sim_config.solver_choice = api_config.get('solver', 'networkx')
        sim_config.H = api_config.get('simulation_time', 20)
        sim_config.d = api_config.get('time_unit', 1)
        sim_config.alpha = api_config.get('alpha', 1.0)
        sim_config.beta = api_config.get('beta', 1.0)
        sim_config.draw = 0 
        sim_config.level_of_simulation = 0
        
        num_agvs = api_config.get('num_agvs', 2)
        sim_config.num_max_agvs = num_agvs
        sim_config.numOfAGVs = num_agvs

        # --- BƯỚC 2: THỰC HIỆN CÁC BƯỚC KHỞI TẠO THEO ĐÚNG THỨ TỰ LOGIC ---
        graph_processor = GraphProcessor()
        graph_processor.print_out = False

        graph_processor.process_input_file(sim_config.filepath)
        graph_processor.H = sim_config.H
        graph_processor.d = sim_config.d
        graph_processor.num_max_agvs = sim_config.num_max_agvs
        graph_processor.alpha = sim_config.alpha
        graph_processor.beta = sim_config.beta
        graph_processor.generate_hm_matrix()
        graph_processor.generate_adj_matrix()

        if not graph_processor.started_nodes:
            graph_processor.ID = []
            graph_processor.earliness = []
            graph_processor.tardiness = []
            count = 0
            while count < graph_processor.num_max_agvs:
                while True:
                    [s, d, e, t] = [np.int64(x) for x in graph_processor.generate_numbers_student(graph_processor.M, graph_processor.H, int(0.2*graph_processor.M))]
                    if s not in graph_processor.started_nodes:
                        break
                graph_processor.started_nodes.append(s)
                graph_processor.ID.append(d)
                graph_processor.earliness.append(e)
                graph_processor.tardiness.append(t)
                count += 1
        
        sim_config.started_nodes = graph_processor.started_nodes
        sim_config.ID = graph_processor.ID
        sim_config.earliness = graph_processor.earliness
        sim_config.tardiness = graph_processor.tardiness

        graph_processor.create_tsg_file()
        
        count = 0
        while count < sim_config.numOfAGVs:
            graph_processor.add_time_windows_constraints()
            count += 1

        restrictions_data = api_config.get('restrictions', [])
        if restrictions_data:
            sim_config.restrictions_data_cache = []
            for r in restrictions_data:
                sim_config.restrictions_data_cache.append((
                    r.get('edges', []), r.get('timeframe', [0, sim_config.H]),
                    r.get('U', 1), r.get('priority', 1.0), None, 2.0
                ))
            sim_config.restrictions_are_set_in_cache = True
            graph_processor.ur = 3
            graph_processor.process_restrictions()

        # --- BƯỚC 3: KHỞI TẠO GRAPH VÀ EVENTS ---
        graph = Graph(graph_processor)
        allAGVs = set()
        events = []
        TASKS = set()
        Event.setValue("number_of_nodes_in_space_graph", graph_processor.M)
        Event.setValue("debug", 0)
        
        graph_processor.init_agvs_n_events(allAGVs, events, graph, graph_processor)
        graph_processor.init_tasks(TASKS)
        graph_processor.init_nodes_n_edges()
        
        events = sorted(events, key=lambda x: x.start_time)
        Event.setValue("allAGVs", allAGVs)

        # --- BƯỚC 4: CHẠY SIMULATOR VÀ BẮT OUTPUT ---
        log_output = ""
        with StdoutCapture() as capture:
            def schedule_events(events_list):
                for event in events_list:
                    discrevpy.simulator.schedule(event.start_time, event.process)
            
            start_time = time.time()
            discrevpy.simulator.ready()
            schedule_events(events)
            discrevpy.simulator.run()
            end_time = time.time()
            
            elapsed_time = end_time - start_time
            hours, rem = divmod(elapsed_time, 3600)
            minutes, seconds = divmod(rem, 60)
            print("Thời gian chạy: {:02}:{:02}:{:02} để giả lập việc di chuyển của {} AGVs".format(int(hours), int(minutes), int(seconds), sim_config.num_max_agvs))

        log_output = capture.get_value()
        solutions = parse_solution_from_log(log_output, graph_processor.M)
        
        with open(sim_config.filepath, 'r') as f:
            map_data_content = f.read()

        return {
            "status": "success",
            "map_data": map_data_content,
            "solutions": solutions,
            "raw_log": log_output,
            "message": "Simulation completed successfully."
        }

    except Exception as e:
        error_full = traceback.format_exc()
        print(error_full)
        return { "status": "error", "message": str(e), "raw_log": error_full }