import sys
import io
import os
import time
import re
from datetime import datetime

# Giả định rằng các file của bạn đã được chuyển vào thư mục `core`
# và chúng ta có thể import chúng trực tiếp.
# Bạn có thể cần sửa lại các đường dẫn import này cho phù hợp với cấu trúc của bạn.
from .model.Graph import Graph
from .model.AGV import AGV
from .model.Event import Event
from .controller.GraphProcessor import GraphProcessor
from .model.Logger import Logger
from . import config as sim_config # Import module config của bạn và đặt tên khác để tránh nhầm lẫn
from .discrevpy import simulator

# --- THAY ĐỔI QUAN TRỌNG ---
# Vì chúng ta không thể dựa vào việc `print` ra console để lấy kết quả,
# chúng ta cần một cách để "bắt" lại output này.
# Phương pháp đơn giản nhất là tạm thời thay thế luồng output chuẩn (stdout).
class StdoutCapture:
    def __init__(self):
        self.buffer = io.StringIO()

    def __enter__(self):
        self._original_stdout = sys.stdout
        sys.stdout = self.buffer
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self._original_stdout

    def get_value(self):
        return self.buffer.getvalue()

# --- HÀM HỖ TRỢ PHÂN TÍCH OUTPUT ---
def parse_solution_from_log(log_output):
    """
    Hàm này sẽ phân tích toàn bộ output dạng text bắt được từ console
    để trích xuất thông tin đường đi của các AGV.
    Bạn cần phải tùy chỉnh các biểu thức chính quy (regex) này cho khớp
    chính xác với định dạng output của chương trình bạn.
    """
    solutions = []
    # Regex để tìm các dòng kết quả, ví dụ: "1===(14)===3===(8.0)===80===END. Total cost: 22.0."
    # và "The total cost of AGV1 is 22.0"
    path_pattern = re.compile(r"(\d+===\(.*===\d+.*END\.)")
    id_pattern = re.compile(r"The total cost of AGV(\d+) is")

    # Tách log thành từng dòng để xử lý
    lines = log_output.splitlines()
    agv_id = None
    
    for line in lines:
        # Tìm ID của AGV trước
        id_match = id_pattern.search(line)
        if id_match:
            agv_id = int(id_match.group(1))

        # Nếu đã có ID, tìm đường đi tương ứng
        path_match = path_pattern.search(line)
        if path_match and agv_id is not None:
            path_str = path_match.group(1)
            
            # Phân tích chuỗi path để ra các bước
            # Ví dụ: "1===(14)===3" -> node 1, time ?, node 3, time 14
            # Đây là phần bạn cần làm chi tiết hơn
            path_details = []
            parts = path_str.split('===')
            current_node = parts[0]
            path_details.append({"node": int(current_node), "time": 0}) # Giả định bắt đầu tại time 0

            # Lặp qua các cặp (thời gian, node)
            for i in range(1, len(parts) - 2, 2):
                time_val = int(re.search(r'\((\d+)\)', parts[i]).group(1))
                node_val = int(parts[i+1])
                path_details.append({"node": node_val, "time": time_val})
            
            solutions.append({
                "agent_id": agv_id,
                "path_string": path_str,
                "path_details": path_details
            })
            agv_id = None # Reset để tìm AGV tiếp theo

    return solutions

# --- HÀM MÔ PHỎNG CHÍNH ---
def run_simulation(api_config):
    """
    Hàm này thay thế toàn bộ file `main.py` cũ.
    Nó nhận một dictionary `api_config` từ Flask server,
    chạy mô phỏng MỘT LẦN, và trả về kết quả dưới dạng dictionary.
    """
    
    # --- BƯỚC 1: SETUP MÔI TRƯỜNG & CONFIG ---
    # Thay vì dùng module config toàn cục, ta sẽ cập nhật nó từ api_config
    sim_config.solver_choice = api_config.get('solver', 'networkx') # Mặc định là networkx
    sim_config.test_automation = 1 # Luôn chạy tự động
    sim_config.level_of_simulation = 2 # Mặc định SFM
    sim_config.filepath = os.path.join('server', 'maps', api_config['map_name'])
    sim_config.H = api_config['simulation_time']
    sim_config.time_unit = api_config.get('time_unit', 1) # Mặc định 1
    
    # Reset lại các biến trạng thái
    allAGVs = set()
    TASKS = set()
    events = []
    AGV.reset()
    simulator.reset()

    # --- BƯỚC 2: CHẠY LOGIC CHÍNH (LẤY TỪ VÒNG LẶP CỦA main.py) ---
    graph_processor = GraphProcessor()

    # Thay vì gọi graph_processor.use_in_main() và chờ input,
    # chúng ta sẽ truyền thẳng config vào.
    # **BẠN CẦN PHẢI SỬA FILE GraphProcessor.py** để nó có thể nhận
    # các thông tin này mà không cần gọi `input()`.
    # Ví dụ: tạo một hàm mới `setup_from_api(self, api_config)`
    graph_processor.setup_from_api(api_config, sim_config)
    
    graph = Graph(graph_processor)
    Event.setValue("number_of_nodes_in_space_graph", graph_processor.M)
    Event.setValue("debug", 0)

    # Khởi tạo AGV và Events từ config
    graph_processor.init_agvs_n_events(allAGVs, events, graph, graph_processor)
    graph_processor.init_tasks(TASKS)
    #graph_processor.init_nodes_n_edges() # Hàm này có thể đã được gọi trong setup_from_api
    
    events = sorted(events, key=lambda x: x.start_time)
    Event.setValue("allAGVs", allAGVs)

    # --- BƯỚC 3: CHẠY MÔ PHỎNG VÀ BẮT LẤY OUTPUT ---
    with StdoutCapture() as capture:
        def schedule_events(events):
            for event in events:
                simulator.schedule(event.start_time, event.process)

        simulator.ready()
        schedule_events(events)
        simulator.run()
    
    # Lấy toàn bộ những gì đã được in ra console
    captured_log = capture.get_value()
    print("--- Captured Log ---")
    print(captured_log) # In ra console của server để debug
    print("--- End Captured Log ---")

    # --- BƯỚC 4: PHÂN TÍCH OUTPUT VÀ TRẢ VỀ KẾT QUẢ ---
    solutions = parse_solution_from_log(captured_log)

    # Đọc nội dung file map để trả về cho client vẽ
    try:
        with open(sim_config.filepath, 'r') as f:
            map_content = f.read()
    except FileNotFoundError:
        map_content = f"Error: Map file not found at {sim_config.filepath}"


    # Tạo object kết quả cuối cùng để trả về dưới dạng JSON
    final_result = {
        "status": "success",
        "solutions": solutions,
        "map_data": map_content,
        "raw_log": captured_log # Gửi kèm log thô để debug phía client nếu cần
    }

    return final_result