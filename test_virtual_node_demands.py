#!/usr/bin/env python3
"""
Test script to demonstrate the virtual node demand functionality
in the modified write_to_file function.
"""

import sys
import os

# Add the current directory to path to import modules
sys.path.append('/home/ubuntu/project/pps-game/simulation/core')

def test_virtual_node_demands():
    """
    Test function to demonstrate how virtual node demands work
    with multiple restrictions.
    """
    print("=== Virtual Node Demand Test ===")
    print()
    
    # Import required modules
    try:
        from controller.GraphProcessor import GraphProcessor
        from controller.RestrictionForTimeFrameController import RestrictionForTimeFrameController
        import config
        
        print("✓ Successfully imported required modules")
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return
    
    # Create GraphProcessor and RestrictionController
    try:
        gp = GraphProcessor()
        restriction_controller = RestrictionForTimeFrameController(gp)
        gp.restriction_controller = restriction_controller
        
        print("✓ Created GraphProcessor and RestrictionForTimeFrameController")
    except Exception as e:
        print(f"✗ Error creating objects: {e}")
        return
    
    # Simulate multiple restrictions with different virtual flows
    print("\n--- Testing Virtual Node Demand Mapping ---")
    
    # Test restriction 1: virtual_flow_needed = 5
    virtual_flow_1 = 5
    vS_global_id_1 = 1001
    vD_global_id_1 = 1002
    
    # Test restriction 2: virtual_flow_needed = 3
    virtual_flow_2 = 3
    vS_global_id_2 = 1003
    vD_global_id_2 = 1004
    
    # Manually set virtual node demands (simulating what apply_restriction does)
    restriction_controller._virtual_node_demands = {
        vS_global_id_1: virtual_flow_1,
        vD_global_id_1: -virtual_flow_1,
        vS_global_id_2: virtual_flow_2,
        vD_global_id_2: -virtual_flow_2
    }
    
    print(f"Set virtual demands for restriction 1:")
    print(f"  vS_global_id {vS_global_id_1}: demand = {virtual_flow_1}")
    print(f"  vD_global_id {vD_global_id_1}: demand = {-virtual_flow_1}")
    
    print(f"Set virtual demands for restriction 2:")
    print(f"  vS_global_id {vS_global_id_2}: demand = {virtual_flow_2}")
    print(f"  vD_global_id {vD_global_id_2}: demand = {-virtual_flow_2}")
    
    # Test the get_virtual_node_demand method
    print("\n--- Testing get_virtual_node_demand method ---")
    for node_id in [vS_global_id_1, vD_global_id_1, vS_global_id_2, vD_global_id_2, 999]:
        demand = restriction_controller.get_virtual_node_demand(node_id)
        print(f"Node {node_id}: demand = {demand}")
    
    # Test get_virtual_node_demands method
    print("\n--- Testing get_virtual_node_demands method ---")
    all_demands = restriction_controller.get_virtual_node_demands()
    print(f"All virtual node demands: {all_demands}")
    
    # Demonstrate how write_to_file would handle these nodes
    print("\n--- Simulating write_to_file logic ---")
    test_nodes = [vS_global_id_1, vD_global_id_1, vS_global_id_2, vD_global_id_2, 1, 50]
    
    for node_id in test_nodes:
        # Simulate the logic from write_to_file
        virtual_demand = restriction_controller.get_virtual_node_demand(node_id)
        
        if virtual_demand != 0:
            demand = virtual_demand
            node_type = "Virtual restriction node"
        else:
            # This would be the original logic for regular nodes
            demand = 0  # simplified for demo
            node_type = "Regular node"
        
        print(f"Node {node_id} ({node_type}): demand = {demand}")
    
    print("\n=== Test completed successfully ===")

if __name__ == "__main__":
    test_virtual_node_demands()
