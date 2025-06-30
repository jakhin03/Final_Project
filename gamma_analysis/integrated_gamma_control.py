#!/usr/bin/env python3
"""
Integrated Gamma Control and Violation Detection System
======================================================

This module integrates gamma control testing directly into the RestrictionForTimeFrameController
and provides violation detection through flow analysis of escape edges.
"""

import os
import shutil
from typing import List, Dict, Tuple, Optional
import networkx as nx
from model.NXSolution import NetworkXSolution

class GammaControlIntegrator:
    """
    Integrates gamma control testing and violation detection into the restriction system.
    """
    
    def __init__(self, restriction_controller):
        self.restriction_controller = restriction_controller
        self.tsg_backup_file = "TSG_backup.txt"
        self.violation_history = []
        self.gamma_test_results = []
        
    def backup_tsg_file(self, tsg_file="TSG.txt"):
        """Create backup of current TSG file."""
        if os.path.exists(tsg_file):
            shutil.copy2(tsg_file, self.tsg_backup_file)
            print(f"📄 TSG backup created: {self.tsg_backup_file}")
            return True
        return False
    
    def restore_tsg_file(self, tsg_file="TSG.txt"):
        """Restore TSG file from backup."""
        if os.path.exists(self.tsg_backup_file):
            shutil.copy2(self.tsg_backup_file, tsg_file)
            print(f"🔄 TSG restored from backup")
            return True
        return False
    
    def detect_escape_edges(self, tsg_file="TSG.txt"):
        """
        Detect escape edges in the TSG file.
        Returns list of escape edges with their gamma costs.
        """
        escape_edges = []
        
        try:
            with open(tsg_file, 'r') as file:
                for line_num, line in enumerate(file, 1):
                    if line.startswith('a '):
                        parts = line.strip().split()
                        if len(parts) >= 6:
                            source = int(parts[1])
                            dest = int(parts[2])
                            cost = int(parts[5])
                            
                            # Check if this is an artificial edge with gamma cost
                            # Based on RestrictionForTimeFrameController logic
                            if source > 80 and dest > 80 and cost > 0:
                                escape_edges.append({
                                    'source': source,
                                    'dest': dest,
                                    'cost': cost,
                                    'line': line_num,
                                    'is_escape_edge': True
                                })
                            
        except FileNotFoundError:
            print(f"❌ TSG file not found: {tsg_file}")
            
        return escape_edges
    
    def analyze_escape_edge_flow(self, escape_edges, tsg_file="TSG.txt"):
        """
        Analyze flow through escape edges to detect violations.
        """
        if not escape_edges:
            print("❌ No escape edges found for flow analysis")
            return []
        
        try:
            # Use NetworkXSolution to analyze flow
            nx_solution = NetworkXSolution()
            nx_solution.read_dimac_file(tsg_file)
            flow_dict = nx_solution.flowDict
            
            violations = []
            total_violation_flow = 0
            total_penalty_cost = 0
            
            print(f"\n🔍 ESCAPE EDGE FLOW ANALYSIS:")
            print(f"{'='*40}")
            
            for edge in escape_edges:
                source_str = str(edge['source'])
                dest_str = str(edge['dest'])
                gamma_cost = edge['cost']
                
                # Check flow through this escape edge
                flow_value = 0
                if source_str in flow_dict and dest_str in flow_dict[source_str]:
                    flow_value = flow_dict[source_str][dest_str]
                
                print(f"Escape Edge {edge['source']} → {edge['dest']}:")
                print(f"  ├── Gamma cost: {gamma_cost}")
                print(f"  ├── Flow: {flow_value}")
                print(f"  └── Status: {'🚨 VIOLATION' if flow_value > 0 else '✅ No violation'}")
                
                if flow_value > 0:
                    violation_cost = flow_value * gamma_cost
                    violations.append({
                        'source': edge['source'],
                        'dest': edge['dest'],
                        'flow': flow_value,
                        'gamma_cost': gamma_cost,
                        'penalty_cost': violation_cost
                    })
                    total_violation_flow += flow_value
                    total_penalty_cost += violation_cost
            
            if violations:
                print(f"\n🚨 VIOLATIONS DETECTED:")
                print(f"  Total escape edges with violations: {len(violations)}")
                print(f"  Total violation flow: {total_violation_flow}")
                print(f"  Total penalty cost: {total_penalty_cost}")
            else:
                print(f"\n✅ NO VIOLATIONS: All restrictions satisfied")
            
            return violations
            
        except Exception as e:
            print(f"❌ Error analyzing escape edge flow: {e}")
            return []
    
    def test_gamma_values(self, gamma_values: List[float], run_simulation_func):
        """
        Test different gamma values and measure violations.
        
        Args:
            gamma_values: List of gamma values to test
            run_simulation_func: Function that runs the simulation and generates TSG
        """
        print(f"🧪 TESTING GAMMA VALUES: {gamma_values}")
        print(f"{'='*60}")
        
        # Backup original restrictions
        original_restrictions = self.restriction_controller.restrictions.copy()
        
        results = []
        
        for gamma in gamma_values:
            print(f"\n🎯 Testing Gamma = {gamma}")
            print(f"{'-'*30}")
            
            # Update gamma in all restrictions
            updated_restrictions = []
            for restriction in original_restrictions:
                restriction_edges, timeframe, U, priority, _, k_val = restriction
                updated_restrictions.append((restriction_edges, timeframe, U, priority, gamma, k_val))
            
            # Set updated restrictions
            self.restriction_controller.restrictions = updated_restrictions
            
            try:
                # Run simulation with new gamma
                print(f"Running simulation with gamma = {gamma}...")
                run_simulation_func()
                
                # Analyze results
                escape_edges = self.detect_escape_edges()
                violations = self.analyze_escape_edge_flow(escape_edges)
                
                # Store results
                result = {
                    'gamma': gamma,
                    'escape_edges_count': len(escape_edges),
                    'violations_count': len(violations),
                    'total_violation_flow': sum(v['flow'] for v in violations),
                    'total_penalty_cost': sum(v['penalty_cost'] for v in violations),
                    'violations': violations
                }
                results.append(result)
                
                print(f"Results for γ = {gamma}:")
                print(f"  Escape edges: {result['escape_edges_count']}")
                print(f"  Violations: {result['violations_count']}")
                print(f"  Total penalty: {result['total_penalty_cost']}")
                
            except Exception as e:
                print(f"❌ Error testing gamma {gamma}: {e}")
                results.append({
                    'gamma': gamma,
                    'error': str(e),
                    'violations_count': -1
                })
        
        # Restore original restrictions
        self.restriction_controller.restrictions = original_restrictions
        
        # Print summary
        self.print_gamma_test_summary(results)
        self.gamma_test_results = results
        return results
    
    def print_gamma_test_summary(self, results: List[Dict]):
        """Print summary of gamma testing results."""
        print(f"\n📊 GAMMA TEST SUMMARY")
        print(f"{'='*50}")
        print(f"{'Gamma':<10} {'Violations':<12} {'Penalty Cost':<15} {'Status':<10}")
        print(f"{'-'*50}")
        
        for result in results:
            if 'error' in result:
                print(f"{result['gamma']:<10} {'ERROR':<12} {'N/A':<15} {'❌':<10}")
            else:
                status = "✅" if result['violations_count'] == 0 else "🚨"
                print(f"{result['gamma']:<10} {result['violations_count']:<12} {result['total_penalty_cost']:<15} {status:<10}")
        
        # Analysis
        successful_results = [r for r in results if 'error' not in r]
        if len(successful_results) >= 2:
            print(f"\n💡 GAMMA CONTROL ANALYSIS:")
            
            # Sort by gamma value
            successful_results.sort(key=lambda x: x['gamma'])
            
            # Check if higher gamma reduces violations
            gamma_effect_confirmed = True
            for i in range(1, len(successful_results)):
                prev_violations = successful_results[i-1]['violations_count']
                curr_violations = successful_results[i]['violations_count']
                if curr_violations > prev_violations:
                    gamma_effect_confirmed = False
                    break
            
            if gamma_effect_confirmed:
                print(f"  ✅ Gamma control confirmed: Higher γ → Fewer violations")
            else:
                print(f"  ⚠️  Gamma effect unclear: Check restriction configuration")
            
            # Show trend
            min_gamma = min(r['gamma'] for r in successful_results)
            max_gamma = max(r['gamma'] for r in successful_results)
            min_violations = next(r['violations_count'] for r in successful_results if r['gamma'] == min_gamma)
            max_violations = next(r['violations_count'] for r in successful_results if r['gamma'] == max_gamma)
            
            print(f"  📈 Violation range: {min_violations} (γ={max_gamma}) to {max_violations} (γ={min_gamma})")

def create_integrated_gamma_tester(restriction_controller):
    """
    Factory function to create an integrated gamma tester for a restriction controller.
    """
    return GammaControlIntegrator(restriction_controller)

# Usage example for integration into main.py
def run_gamma_experiment_with_main():
    """
    Example of how to integrate gamma testing into the main simulation loop.
    """
    print("🎯 INTEGRATED GAMMA EXPERIMENT")
    print("This should be called from within main.py after creating RestrictionForTimeFrameController")
    print()
    print("Example integration:")
    print("""
    # In main.py, after creating restriction_controller:
    restriction_controller = RestrictionForTimeFrameController(graph_processor)
    gamma_tester = create_integrated_gamma_tester(restriction_controller)
    
    # Define gamma values to test
    gamma_values = [50, 100, 200, 400]
    
    # Define simulation runner function
    def run_simulation():
        restriction_controller.apply_restriction()
        # ... rest of simulation logic from main.py
        # This should generate TSG.txt
    
    # Run gamma experiments
    results = gamma_tester.test_gamma_values(gamma_values, run_simulation)
    """)

if __name__ == "__main__":
    run_gamma_experiment_with_main()
