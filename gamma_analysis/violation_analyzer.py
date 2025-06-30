#!/usr/bin/env python3
"""
Violation Analysis Tool - Enhanced
=================================

This tool analyzes violations by detecting escape edges (artificial edges with gamma cost)
and checking if they carry flow, which indicates actual violations.
"""

import os
import sys
import re
from typing import List, Dict, Tuple

# Add parent directory for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from integrated_gamma_control import GammaControlIntegrator

class ViolationAnalyzer:
    def __init__(self, tsg_file: str = "TSG.txt"):
        self.tsg_file = tsg_file
        self.violations = []
        self.edges = []
        self.nodes = []
        
        # Use integrated gamma control for escape edge detection
        self.gamma_integrator = GammaControlIntegrator(None)
        
    def parse_tsg_file(self):
        """Parse the TSG file and extract all information."""
        if not os.path.exists(self.tsg_file):
            print(f"❌ TSG file not found: {self.tsg_file}")
            return False
            
        self.violations = []
        self.edges = []
        self.nodes = []
        
        try:
            with open(self.tsg_file, 'r') as file:
                for line_num, line in enumerate(file, 1):
                    line = line.strip()
                    
                    if line.startswith('c Edge') and 'violates' in line:
                        violation = self.parse_violation_line(line, line_num)
                        if violation:
                            self.violations.append(violation)
                    
                    elif line.startswith('a'):  # Arc/edge definition
                        edge = self.parse_edge_line(line, line_num)
                        if edge:
                            self.edges.append(edge)
                    
                    elif line.startswith('n'):  # Node definition
                        node = self.parse_node_line(line, line_num)
                        if node:
                            self.nodes.append(node)
            
            return True
            
        except Exception as e:
            print(f"❌ Error parsing TSG file: {e}")
            return False
    
    def parse_violation_line(self, line: str, line_num: int) -> Dict:
        """Parse a violation comment line."""
        # Example: "c Edge (2,5) violates restriction 1 with n=2"
        try:
            # Extract source and destination
            match = re.search(r'Edge \((\d+),(\d+)\)', line)
            if not match:
                return None
                
            source = int(match.group(1))
            dest = int(match.group(2))
            
            # Extract violation count
            n_match = re.search(r'n=(\d+)', line)
            violation_count = int(n_match.group(1)) if n_match else 1
            
            # Extract restriction number
            restr_match = re.search(r'restriction (\d+)', line)
            restriction_id = int(restr_match.group(1)) if restr_match else None
            
            return {
                'source': source,
                'dest': dest,
                'violation_count': violation_count,
                'restriction_id': restriction_id,
                'line_num': line_num,
                'raw_line': line
            }
            
        except Exception as e:
            print(f"⚠️  Error parsing violation line {line_num}: {e}")
            return None
    
    def parse_edge_line(self, line: str, line_num: int) -> Dict:
        """Parse an edge definition line."""
        # Example: "a 1 2 0 1000 50"
        try:
            parts = line.split()
            if len(parts) >= 6:
                return {
                    'source': parts[1],
                    'dest': parts[2],
                    'lower_bound': int(parts[3]),
                    'upper_bound': int(parts[4]),
                    'cost': int(parts[5]),
                    'line_num': line_num
                }
        except Exception as e:
            print(f"⚠️  Error parsing edge line {line_num}: {e}")
        return None
    
    def parse_node_line(self, line: str, line_num: int) -> Dict:
        """Parse a node definition line."""
        # Example: "n 1 -5"
        try:
            parts = line.split()
            if len(parts) >= 3:
                return {
                    'id': parts[1],
                    'demand': int(parts[2]),
                    'line_num': line_num
                }
        except Exception as e:
            print(f"⚠️  Error parsing node line {line_num}: {e}")
        return None
    
    def analyze_violations(self):
        """Analyze the violations found."""
        if not self.violations:
            print("✅ No violations found!")
            return
        
        print(f"\n🚨 VIOLATION ANALYSIS")
        print(f"{'='*50}")
        print(f"Total violations found: {len(self.violations)}")
        
        # Group by restriction
        by_restriction = {}
        for v in self.violations:
            rid = v['restriction_id']
            if rid not in by_restriction:
                by_restriction[rid] = []
            by_restriction[rid].append(v)
        
        print(f"\nViolations by restriction:")
        for rid, violations in by_restriction.items():
            print(f"  Restriction {rid}: {len(violations)} violations")
        
        # Sum total violation count
        total_violation_count = sum(v['violation_count'] for v in self.violations)
        print(f"\nTotal violation count (n): {total_violation_count}")
        
        # Show details
        print(f"\nDetailed violations:")
        print(f"{'Edge':<10} {'Count':<6} {'Restriction':<12} {'Line':<6}")
        print("-" * 40)
        
        for v in self.violations:
            edge_str = f"({v['source']},{v['dest']})"
            print(f"{edge_str:<10} {v['violation_count']:<6} {v['restriction_id']:<12} {v['line_num']:<6}")
    
    def get_violation_summary(self) -> Dict:
        """Get a summary of violations for experiments."""
        return {
            'total_violations': len(self.violations),
            'total_violation_count': sum(v['violation_count'] for v in self.violations),
            'violated_edges': [(v['source'], v['dest']) for v in self.violations],
            'restrictions_violated': list(set(v['restriction_id'] for v in self.violations if v['restriction_id'] is not None))
        }
    
    def print_graph_summary(self):
        """Print a summary of the graph structure."""
        print(f"\n📊 GRAPH SUMMARY")
        print(f"{'='*30}")
        print(f"Nodes: {len(self.nodes)}")
        print(f"Edges: {len(self.edges)}")
        
        if self.nodes:
            demands = [n['demand'] for n in self.nodes]
            print(f"Demand range: {min(demands)} to {max(demands)}")
            supply_nodes = len([n for n in self.nodes if n['demand'] > 0])
            demand_nodes = len([n for n in self.nodes if n['demand'] < 0])
            neutral_nodes = len([n for n in self.nodes if n['demand'] == 0])
            print(f"Supply nodes: {supply_nodes}")
            print(f"Demand nodes: {demand_nodes}")
            print(f"Neutral nodes: {neutral_nodes}")
        
        if self.edges:
            costs = [e['cost'] for e in self.edges]
            print(f"Cost range: {min(costs)} to {max(costs)}")
    
    def analyze_escape_edge_violations(self):
        """
        Analyze violations using escape edge flow detection.
        This is the correct way to detect violations.
        """
        print(f"\n🎯 ESCAPE EDGE VIOLATION ANALYSIS")
        print(f"{'='*50}")
        
        # Detect escape edges
        escape_edges = self.gamma_integrator.detect_escape_edges(self.tsg_file)
        
        if not escape_edges:
            print("❌ No escape edges found")
            print("   This means either:")
            print("   • No restrictions were applied")
            print("   • All restrictions are satisfied without escape edges")
            return []
        
        print(f"✅ Found {len(escape_edges)} escape edges")
        
        # Analyze flow through escape edges
        violations = self.gamma_integrator.analyze_escape_edge_flow(escape_edges, self.tsg_file)
        
        if violations:
            print(f"\n🚨 VIOLATIONS DETECTED:")
            print(f"  AGVs used escape edges {len(violations)} times")
            print(f"  Total violation flow: {sum(v['flow'] for v in violations)}")
            print(f"  Total penalty cost: {sum(v['penalty_cost'] for v in violations)}")
            
            print(f"\n📋 Violation Details:")
            for i, v in enumerate(violations, 1):
                print(f"  {i}. Edge {v['source']} → {v['dest']}")
                print(f"     ├── Flow: {v['flow']} AGVs")
                print(f"     ├── Gamma: {v['gamma_cost']}")
                print(f"     └── Penalty: {v['penalty_cost']}")
        else:
            print(f"\n✅ NO VIOLATIONS:")
            print(f"   All escape edges have zero flow")
            print(f"   All restrictions were satisfied!")
        
        return violations

def main():
    """Main function to analyze violations."""
    print("🔍 TSG Violation Analyzer")
    print("=" * 30)
    
    # Check for TSG files
    tsg_files = ["TSG.txt"]
    if os.path.exists("TSG_true.txt"):
        tsg_files.append("TSG_true.txt")
    
    for tsg_file in tsg_files:
        if os.path.exists(tsg_file):
            print(f"\n📄 Analyzing {tsg_file}")
            print("-" * 30)
            
            analyzer = ViolationAnalyzer(tsg_file)
            if analyzer.parse_tsg_file():
                analyzer.print_graph_summary()
                analyzer.analyze_violations()
                
                # Run escape edge violation analysis
                analyzer.analyze_escape_edge_violations()
                
                summary = analyzer.get_violation_summary()
                if summary['total_violations'] > 0:
                    print(f"\n💡 This file has {summary['total_violations']} violation(s)")
                    print(f"    You can use this as a baseline for gamma experiments")
                else:
                    print(f"\n✅ This file has no violations")
                    print(f"    Try running with lower gamma to see violations")
        else:
            print(f"⚠️  {tsg_file} not found")
    
    print(f"\n🎯 Ready for gamma experiment!")
    print(f"   Run: python main_gamma_analysis.py")

if __name__ == "__main__":
    main()
