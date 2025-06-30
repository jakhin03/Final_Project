# Unit Tests for RestrictionForTimeFrameController

This file contains comprehensive unit tests for the `RestrictionForTimeFrameController` class, following best practices for unit testing with proper mocking and isolation.

## Test Philosophy

The tests follow these principles:

1. **Mock External Dependencies**: Uses mock objects for `GraphProcessor` to avoid dependency on large external systems
2. **Test Individual Units**: Each test focuses on a specific method or behavior 
3. **Automated and Fast**: All tests run automatically without user input
4. **Isolated**: Each test is independent and can run in any order

## Test Coverage

### 1. Tests for `identify_restricted_edges()`

- **`test_identify_edges_with_full_match()`**: Tests edge identification when spatial edge and timeframe fully match
- **`test_identify_edges_with_no_spatial_match()`**: Tests when spatial edge doesn't exist in TSG
- **`test_identify_edges_with_no_temporal_match()`**: Tests when timeframe doesn't overlap with edge times
- **`test_identify_edges_with_partial_temporal_match()`**: Tests partial temporal overlap scenarios

### 2. Tests for `calculate_max_flow()`

- **`test_calculate_max_flow_simple_case()`**: Tests max flow calculation with NetworkX integration using parallel edges

### 3. Tests for `apply_restriction()` (Core Logic)

- **`test_apply_restriction_when_F_less_than_U()`**: Tests when max flow F < capacity limit U (no modification needed)
- **`test_apply_restriction_when_F_greater_than_U()`**: Tests when max flow F > capacity limit U (artificial nodes/edges created)
- **`test_apply_restriction_removes_original_edges()`**: Tests that graph structure is properly modified

### 4. Tests for `remove_artificial_artifact()`

- **`test_cleanup_restores_graph_state()`**: Tests that cleanup properly restores graph state

### 5. Helper Method Tests

- **`test_identify_restricted_nodes()`**: Tests node identification from omega
- **`test_calculate_incoming_capacity_for_restricted_nodes()`**: Tests incoming capacity calculation
- **`test_calculate_outgoing_capacity_for_restricted_nodes()`**: Tests outgoing capacity calculation
- **`test_calculate_virtual_flow()`**: Tests virtual flow calculation logic

## Key Testing Patterns

### Mock Setup
```python
# Create mock GraphProcessor with controlled TSG structure
self.mock_graph_processor = Mock()
self.mock_graph_processor.M = 3  # 3x3 grid
self.mock_graph_processor.ts_edges = [
    (1, 4, 0, 1, 10),  # spatial (1,1) from time 0 to time 1
    (4, 5, 0, 1, 5),   # spatial (1,2) horizontal edge at time 1
    # ... more edges
]
```

### Test Structure
```python
def test_method_name(self):
    # Given: Setup test conditions
    restriction_edges = [[1, 2]]
    
    # When: Call the method under test  
    result = self.controller.identify_restricted_edges(...)
    
    # Then: Assert expected behavior
    self.assertEqual(len(result), expected_count)
```

### Mocking Strategy
- Mock `GraphProcessor` to provide controlled test data
- Mock `calculate_max_flow()` to return predetermined values
- Mock `get_restrictions()` to bypass user input

## Node ID Mapping

The tests assume the following TSG node ID mapping:
- **Formula**: `node_id = spatial_coordinate + time * M`
- **Time starts from 0**
- **For M=3 (3x3 grid)**:
  - Time 0: nodes 1,2,3 (spatial coordinates 1,2,3)
  - Time 1: nodes 4,5,6 (spatial coordinates 1,2,3)  
  - Time 2: nodes 7,8,9 (spatial coordinates 1,2,3)

## Running the Tests

```bash
# Run all tests
python3 test_restriction_for_timeframe_controller.py

# Run with verbose output
python3 test_restriction_for_timeframe_controller.py -v

# Run specific test
python3 -m unittest test_restriction_for_timeframe_controller.TestRestrictionForTimeFrameController.test_identify_edges_with_full_match
```

## Benefits of This Testing Approach

1. **Fast Execution**: No external dependencies, runs in milliseconds
2. **Reliable**: Deterministic results, no random failures
3. **Comprehensive**: Covers all major logic paths and edge cases
4. **Maintainable**: Clear test structure makes it easy to add new tests
5. **Debugging Friendly**: Isolated tests make it easy to identify issues

## Future Enhancements

- Add performance tests for large TSG graphs
- Add integration tests that combine multiple components
- Add property-based tests for edge cases
- Add tests for concurrent restriction applications
