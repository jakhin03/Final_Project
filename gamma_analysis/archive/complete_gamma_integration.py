#!/usr/bin/env python3
"""
Complete Gamma Control Integration Example
=========================================

This script demonstrates how to integrate gamma control and violation detection
into the main simulation pipeline.
"""

import sys
import os
import time
from controller.GraphProcessor import GraphProcessor
from controller.RestrictionForTimeFrameController import RestrictionForTimeFrameController
from model.Graph import Graph
from model.Event import Event
from discrevpy import simulator
import config

def run_simulation_with_gamma_analysis():
    """
    Run a complete simulation with gamma analysis integration.
    This is based on the main.py logic but focused on gamma control.
    """
    print("🎯 COMPLETE GAMMA CONTROL INTEGRATION TEST")
    print("=" * 60)
    
    # Initialize components (similar to main.py)
    graph_processor = GraphProcessor()
    graph_processor.use_in_main(automated=True)  # Use automation mode
    
    # Create restriction controller with gamma integration
    restriction_controller = RestrictionForTimeFrameController(graph_processor)
    
    # Enable gamma control
    gamma_integrator = restriction_controller.enable_gamma_control()
    
    # Set up restrictions (example from main.py run)
    test_restrictions = [
        # (restriction_edges, timeframe, U, priority, gamma, k_val)
        ([[[1, 2]]], [3, 4], 1, 1.0, None, 2.0)  # Will use auto-calculated gamma
    ]
    
    if not restriction_controller.set_restrictions(test_restrictions):
        print("❌ Failed to set restrictions")
        return
    
    print(f"✅ Restrictions configured: {len(test_restrictions)} restriction(s)")
    
    # Test different gamma values
    gamma_values = [50, 100, 200, 400, 800]
    
    def simulation_runner():
        """Run one complete simulation cycle."""
        print("  📊 Running simulation cycle...")
        
        # Apply restrictions (this creates the escape edges)
        restriction_controller.apply_restriction()
        
        # Initialize graph and simulation components
        graph = Graph(graph_processor)
        events = []
        Event.setValue("number_of_nodes_in_space_graph", graph_processor.M)
        Event.setValue("debug", 0)
        
        # Initialize AGVs and events (simplified from main.py)
        allAGVs = set()
        TASKS = set()
        graph_processor.init_agvs_n_events(allAGVs, events, graph, graph_processor)
        graph_processor.init_tasks(TASKS)
        graph_processor.init_nodes_n_edges()
        
        # Sort events and run simulation
        events = sorted(events, key=lambda x: x.start_time)
        Event.setValue("allAGVs", allAGVs)
        
        # Schedule and run simulation
        simulator.ready()
        for event in events:
            simulator.schedule(event.start_time, event.process)
        
        # This should generate TSG.txt with escape edges
        try:
            simulator.run()
            print("  ✅ Simulation completed")
        except Exception as e:
            print(f"  ⚠️  Simulation had issues: {e}")
        
        # Reset for next run
        simulator.reset()
        config.totalCost = 0
        config.reachingTargetAGVs = 0
        config.haltingAGVs = 0
    
    # Run gamma impact test
    print(f"\n🧪 Testing gamma values: {gamma_values}")
    results = restriction_controller.test_gamma_impact(gamma_values, simulation_runner)
    
    # Analyze current state (latest TSG)
    print(f"\n🔍 Analyzing final state...")
    violations = restriction_controller.analyze_current_violations()
    summary = restriction_controller.get_violation_summary()
    
    print(f"\n📋 FINAL SUMMARY:")
    print(f"  Escape edges found: {summary['escape_edges_count']}")
    print(f"  Active violations: {summary['violations_count']}")
    print(f"  Total penalty cost: {summary['total_penalty_cost']}")
    
    if summary['violations_count'] > 0:
        print(f"  🚨 Violated edges: {summary['violated_edges']}")
        print(f"  💡 Try increasing gamma to reduce violations")
    else:
        print(f"  ✅ No violations - all restrictions satisfied")
    
    # Clean up
    restriction_controller.remove_artificial_artifact()
    
    return results, summary

def quick_gamma_test():
    """
    Quick test to verify gamma control is working.
    """
    print("⚡ QUICK GAMMA CONTROL TEST")
    print("=" * 40)
    
    # Just check if we can detect escape edges in existing TSG
    if os.path.exists("TSG.txt"):
        from integrated_gamma_control import GammaControlIntegrator
        
        # Create a dummy controller for testing
        class DummyController:
            def __init__(self):
                self.restrictions = []
        
        dummy_controller = DummyController()
        integrator = GammaControlIntegrator(dummy_controller)
        
        escape_edges = integrator.detect_escape_edges("TSG.txt")
        print(f"📊 Found {len(escape_edges)} escape edges in existing TSG.txt")
        
        for edge in escape_edges:
            print(f"  Edge {edge['source']} → {edge['dest']} (γ = {edge['cost']})")
        
        if escape_edges:
            violations = integrator.analyze_escape_edge_flow(escape_edges, "TSG.txt")
            print(f"🚨 Detected {len(violations)} violations")
        else:
            print("❌ No escape edges found. Run main.py first to generate TSG with restrictions.")
    else:
        print("❌ No TSG.txt found. Run main.py first.")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        quick_gamma_test()
    else:
        try:
            results, summary = run_simulation_with_gamma_analysis()
            print(f"\n🏁 INTEGRATION TEST COMPLETE")
            print(f"Gamma control and violation detection successfully integrated!")
        except Exception as e:
            print(f"❌ Integration test failed: {e}")
            import traceback
            traceback.print_exc()
