# Tóm tắt thay đổi: Virtual Node Demand trong write_to_file

## Mô tả
Đã chỉnh sửa hàm `write_to_file` của `GraphProcessor` để xử lý đúng giá trị demand cho các nút ảo (virtual nodes) được tạo bởi các ràng buộc (restrictions). Mỗi restriction tạo ra một cặp nút ảo toàn cục (vS_global_id, vD_global_id) với giá trị demand tương ứng với virtual_flow_needed.

## Các thay đổi chính

### 1. RestrictionForTimeFrameController.py

#### Thêm thuộc tính tracking virtual node demands:
```python
# --- VIRTUAL FLOW MAPPING ---
# Map virtual node IDs to their virtual flow values
# Format: {vS_global_id: virtual_flow_needed, vD_global_id: -virtual_flow_needed}
self._virtual_node_demands = {}
```

#### Cập nhật apply_restriction() để lưu virtual node demands:
```python
# Track virtual flow demands for these nodes
self._virtual_node_demands[vS_global_id] = virtual_flow_needed
self._virtual_node_demands[vD_global_id] = -virtual_flow_needed
```

#### Thêm các phương thức truy cập:
```python
def get_virtual_node_demands(self) -> Dict[int, int]:
    """Get mapping of virtual node IDs to their demand values."""
    return self._virtual_node_demands.copy()

def get_virtual_node_demand(self, node_id: int) -> int:
    """Get demand value for a specific virtual node."""
    return self._virtual_node_demands.get(node_id, 0)
```

#### Cập nhật remove_artificial_artifact() để dọn dẹp:
```python
self._virtual_node_demands = {}  # Clear virtual node demands
```

### 2. GraphProcessor.py

#### Chỉnh sửa write_to_file() để sử dụng virtual node demands:
```python
def write_to_file(self):
    # ...existing code...
    for node in self.ts_nodes:
        # ...existing code...
        
        # Check if this is a virtual restriction node with specific demand
        virtual_demand = 0
        if self.restriction_controller and hasattr(self.restriction_controller, 'get_virtual_node_demand'):
            virtual_demand = self.restriction_controller.get_virtual_node_demand(node.id)
        
        # Calculate demand: virtual nodes have their specific demand, others follow original logic
        if virtual_demand != 0:
            demand = virtual_demand
            if self.print_out:
                print(f"Virtual restriction node {node.id}: demand = {demand}")
        else:
            demand = 1 if node.id in self.started_nodes else -1 if node.id in [target.id for target in self.target_nodes] else 0
            
        file.write(f"n {node.id} {demand}\n")
    # ...existing code...
```

## Luồng hoạt động

1. **Khi apply_restriction() được gọi:**
   - Với mỗi restriction có virtual_flow_needed > 0
   - Tạo vS_global_id và vD_global_id
   - Lưu: `_virtual_node_demands[vS_global_id] = virtual_flow_needed`
   - Lưu: `_virtual_node_demands[vD_global_id] = -virtual_flow_needed`

2. **Khi write_to_file() được gọi:**
   - Với mỗi node trong ts_nodes
   - Kiểm tra xem node có phải là virtual restriction node không
   - Nếu có: dùng demand từ `_virtual_node_demands`
   - Nếu không: dùng logic gốc (started=1, target=-1, khác=0)

3. **Khi remove_artificial_artifact() được gọi:**
   - Xóa tất cả virtual nodes và edges
   - Reset `_virtual_node_demands = {}`

## Ví dụ

### Với 2 restrictions:
- Restriction 1: virtual_flow_needed = 5
  - vS_global_id = 1001 → demand = +5
  - vD_global_id = 1002 → demand = -5

- Restriction 2: virtual_flow_needed = 3
  - vS_global_id = 1003 → demand = +3
  - vD_global_id = 1004 → demand = -3

### File TSG.txt sẽ có:
```
n 1001 5     # Virtual source cho restriction 1
n 1002 -5    # Virtual sink cho restriction 1
n 1003 3     # Virtual source cho restriction 2
n 1004 -3    # Virtual sink cho restriction 2
n 1 1        # Started node bình thường
n 50 -1      # Target node bình thường
```

## Lợi ích

1. **Tách biệt rõ ràng:** Mỗi restriction có virtual flow riêng
2. **Mở rộng dễ dàng:** Hỗ trợ nhiều restrictions cùng lúc
3. **Bảo toàn logic gốc:** Các node bình thường vẫn hoạt động như cũ
4. **Dễ debug:** In ra thông tin virtual node khi cần thiết
5. **Cleanup tự động:** Tự động dọn dẹp khi remove restrictions
