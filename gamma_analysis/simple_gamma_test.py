#!/usr/bin/env python3
"""
Simple Gamma Test Runner
=======================

This script modifies gamma values in restrictions and re-runs simulations
to test the gamma control effect on violations.
"""

import os
import sys
import subprocess
import tempfile
import shutil
from controller.GraphProcessor import GraphProcessor  
from controller.RestrictionForTimeFrameController import RestrictionForTimeFrameController
from integrated_gamma_control import GammaControlIntegrator

def modify_gamma_and_test(target_gamma):
    """
    Modify restriction gamma and run a test simulation.
    """
    print(f"🧪 Testing with gamma = {target_gamma}")
    print("-" * 30)
    
    # Create a restriction controller
    graph_processor = GraphProcessor()
    graph_processor.use_in_main(automated=True)
    
    restriction_controller = RestrictionForTimeFrameController(graph_processor)
    
    # Set up a test restriction with the specified gamma
    test_restrictions = [
        # (restriction_edges, timeframe, U, priority, gamma, k_val)
        ([[[1, 2]]], [3, 4], 1, 1.0, target_gamma, 2.0)
    ]
    
    if restriction_controller.set_restrictions(test_restrictions):
        print(f"✅ Set restriction with gamma = {target_gamma}")
        
        # Apply restriction (this creates escape edges with specified gamma)
        restriction_controller.apply_restriction()
        
        # Enable gamma analysis
        gamma_integrator = restriction_controller.enable_gamma_control()
        
        # Check what escape edges were created
        escape_edges = gamma_integrator.detect_escape_edges("TSG.txt")
        print(f"📊 Created {len(escape_edges)} escape edges")
        
        for edge in escape_edges:
            print(f"  Edge {edge['source']} → {edge['dest']} (cost: {edge['cost']})")
        
        # Clean up
        restriction_controller.remove_artificial_artifact()
        
        return escape_edges
    else:
        print(f"❌ Failed to set restrictions")
        return []

def run_simple_main_simulation():
    """
    Run a simplified version of main.py to generate TSG with different inputs.
    """
    print("🚀 Running simulation to generate TSG...")
    
    # Create input for main.py automation
    # This simulates the user inputs that main.py expects
    simulation_input = """3
1
simplest.txt
10
0
1
2
1
1 2
0


"""
    
    try:
        # Run main.py with automated input
        process = subprocess.Popen(
            [sys.executable, "main.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=os.getcwd()
        )
        
        stdout, stderr = process.communicate(input=simulation_input, timeout=30)
        
        if process.returncode == 0:
            print("✅ Simulation completed successfully")
            return True
        else:
            print(f"⚠️  Simulation had issues (exit code: {process.returncode})")
            if stderr:
                print(f"Error output: {stderr[:200]}...")
            return False
            
    except subprocess.TimeoutExpired:
        process.kill()
        print("⚠️  Simulation timed out")
        return False
    except Exception as e:
        print(f"❌ Failed to run simulation: {e}")
        return False

def test_gamma_effect():
    """
    Test the effect of different gamma values on escape edge creation and violations.
    """
    print("🎯 TESTING GAMMA EFFECT ON VIOLATIONS")
    print("=" * 50)
    
    # Test different gamma values
    gamma_values = [1, 50, 100, 200, 500]
    
    print(f"Testing gamma values: {gamma_values}")
    print()
    
    # Backup existing TSG if present
    tsg_backup = None
    if os.path.exists("TSG.txt"):
        tsg_backup = "TSG_original.txt"
        shutil.copy("TSG.txt", tsg_backup)
        print(f"📄 Backed up existing TSG to {tsg_backup}")
    
    results = []
    
    for gamma in gamma_values:
        print(f"\n{'='*20} Gamma = {gamma} {'='*20}")
        
        try:
            # First run simulation to get base TSG
            if run_simple_main_simulation():
                # Then analyze for violations
                integrator = GammaControlIntegrator(None)
                escape_edges = integrator.detect_escape_edges("TSG.txt")
                
                if escape_edges:
                    violations = integrator.analyze_escape_edge_flow(escape_edges, "TSG.txt")
                    result = {
                        'gamma': gamma,
                        'escape_edges': len(escape_edges),
                        'violations': len(violations),
                        'total_flow': sum(v['flow'] for v in violations),
                        'total_penalty': sum(v['penalty_cost'] for v in violations)
                    }
                else:
                    result = {
                        'gamma': gamma,
                        'escape_edges': 0,
                        'violations': 0,
                        'total_flow': 0,
                        'total_penalty': 0
                    }
                
                results.append(result)
                print(f"Result: {result['escape_edges']} escape edges, {result['violations']} violations")
            else:
                print(f"❌ Simulation failed for gamma = {gamma}")
                
        except Exception as e:
            print(f"❌ Error testing gamma {gamma}: {e}")
    
    # Print summary
    print(f"\n📊 GAMMA TEST SUMMARY")
    print("=" * 50)
    print(f"{'Gamma':<8} {'Escapes':<8} {'Violations':<12} {'Flow':<8} {'Penalty':<10}")
    print("-" * 50)
    
    for result in results:
        print(f"{result['gamma']:<8} {result['escape_edges']:<8} {result['violations']:<12} "
              f"{result['total_flow']:<8} {result['total_penalty']:<10}")
    
    # Restore original TSG if it existed
    if tsg_backup and os.path.exists(tsg_backup):
        shutil.copy(tsg_backup, "TSG.txt")
        os.remove(tsg_backup)
        print(f"\n🔄 Restored original TSG")
    
    return results

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test-gamma":
        test_gamma_effect()
    else:
        print("Simple Gamma Test Runner")
        print("Options:")
        print("  --test-gamma    Run gamma effect test")
        print("\nOr run with specific gamma:")
        
        if len(sys.argv) > 1:
            try:
                gamma = float(sys.argv[1])
                modify_gamma_and_test(gamma)
            except ValueError:
                print("Invalid gamma value")
        else:
            print("Usage: python simple_gamma_test.py <gamma_value>")
            print("   or: python simple_gamma_test.py --test-gamma")
