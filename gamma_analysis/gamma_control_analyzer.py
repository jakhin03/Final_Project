#!/usr/bin/env python3
"""
Gamma Control Analysis and Visualization Tool
============================================

This tool explores the role of penalty cost (gamma) by running scenarios
with varied gamma values and visualizing the results to demonstrate
gamma's effectiveness as a 'control knob' for balancing rule adherence
and operational efficiency.
"""

import os
import sys
import json
import time
from datetime import datetime
from typing import List, Dict, Tuple
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for headless environments
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# Add parent directory to path for imports
sys.path.append('..')
from integrated_gamma_control import GammaControlIntegrator

class GammaAnalysisRunner:
    """
    Runs comprehensive gamma analysis with visualization capabilities.
    """
    
    def __init__(self, output_dir="output"):
        self.output_dir = output_dir
        self.data_dir = "data"
        self.results = []
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Ensure output directories exist
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)
        
    def run_gamma_experiment(self, gamma_values: List[float], 
                           simulation_runner_func, 
                           experiment_name: str = "gamma_analysis"):
        """
        Run comprehensive gamma experiment across multiple gamma values.
        
        Args:
            gamma_values: List of gamma values to test
            simulation_runner_func: Function that runs simulation and generates TSG
            experiment_name: Name for this experiment
        """
        print(f"🧪 GAMMA CONTROL EXPERIMENT: {experiment_name}")
        print(f"{'='*60}")
        print(f"Testing gamma values: {gamma_values}")
        print(f"Output directory: {self.output_dir}")
        print()
        
        results = []
        
        for i, gamma in enumerate(gamma_values):
            print(f"\n📊 Test {i+1}/{len(gamma_values)}: Gamma = {gamma}")
            print(f"{'-'*40}")
            
            try:
                # Run simulation with this gamma value
                print(f"  🚀 Running simulation with γ = {gamma}...")
                start_time = time.time()
                
                # This should generate TSG.txt with the specified gamma
                simulation_runner_func(gamma)
                
                simulation_time = time.time() - start_time
                
                # Analyze results
                print(f"  🔍 Analyzing violations...")
                integrator = GammaControlIntegrator(None)
                
                # Detect escape edges
                escape_edges = integrator.detect_escape_edges("../TSG.txt")
                
                if not escape_edges:
                    print(f"  ❌ No escape edges found for γ = {gamma}")
                    result = {
                        'gamma': gamma,
                        'escape_edges_count': 0,
                        'violations_count': 0,
                        'total_violation_flow': 0,
                        'total_penalty_cost': 0,
                        'simulation_time': simulation_time,
                        'status': 'no_escape_edges'
                    }
                else:
                    # Analyze flow through escape edges
                    violations = integrator.analyze_escape_edge_flow(escape_edges, "../TSG.txt")
                    
                    result = {
                        'gamma': gamma,
                        'escape_edges_count': len(escape_edges),
                        'violations_count': len(violations),
                        'total_violation_flow': sum(v['flow'] for v in violations),
                        'total_penalty_cost': sum(v['penalty_cost'] for v in violations),
                        'simulation_time': simulation_time,
                        'violations_detail': violations,
                        'escape_edges_detail': escape_edges,
                        'status': 'success'
                    }
                
                results.append(result)
                
                # Print immediate results
                print(f"  ✅ Results for γ = {gamma}:")
                print(f"     • Escape edges: {result['escape_edges_count']}")
                print(f"     • Violations: {result['violations_count']}")
                print(f"     • Violation flow: {result['total_violation_flow']}")
                print(f"     • Penalty cost: {result['total_penalty_cost']}")
                print(f"     • Simulation time: {simulation_time:.2f}s")
                
                # Save intermediate TSG for this gamma
                tsg_file = f"{self.data_dir}/TSG_gamma_{gamma}_{self.timestamp}.txt"
                if os.path.exists("../TSG.txt"):
                    os.system(f"cp ../TSG.txt {tsg_file}")
                    print(f"     • TSG saved: {tsg_file}")
                
            except Exception as e:
                print(f"  ❌ Error with γ = {gamma}: {e}")
                result = {
                    'gamma': gamma,
                    'error': str(e),
                    'status': 'error',
                    'simulation_time': 0
                }
                results.append(result)
        
        # Save results
        self.results = results
        self.save_results(experiment_name)
        
        # Generate analysis and visualization
        self.generate_analysis_report(experiment_name)
        self.create_visualization(experiment_name)
        
        return results
    
    def save_results(self, experiment_name: str):
        """Save experiment results to JSON file."""
        results_file = f"{self.output_dir}/{experiment_name}_results_{self.timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump({
                'experiment_name': experiment_name,
                'timestamp': self.timestamp,
                'results': self.results
            }, f, indent=2)
        
        print(f"\n💾 Results saved to: {results_file}")
    
    def generate_analysis_report(self, experiment_name: str):
        """Generate detailed analysis report."""
        report_file = f"{self.output_dir}/{experiment_name}_analysis_{self.timestamp}.md"
        
        successful_results = [r for r in self.results if r['status'] == 'success']
        
        with open(report_file, 'w') as f:
            f.write(f"# Gamma Control Analysis Report\n\n")
            f.write(f"**Experiment:** {experiment_name}\n")
            f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Total Tests:** {len(self.results)}\n")
            f.write(f"**Successful Tests:** {len(successful_results)}\n\n")
            
            f.write(f"## Summary Results\n\n")
            f.write(f"| Gamma | Escape Edges | Violations | Violation Flow | Penalty Cost | Status |\n")
            f.write(f"|-------|-------------|------------|---------------|-------------|--------|\n")
            
            for result in self.results:
                if result['status'] == 'success':
                    f.write(f"| {result['gamma']} | {result['escape_edges_count']} | "
                           f"{result['violations_count']} | {result['total_violation_flow']} | "
                           f"{result['total_penalty_cost']} | ✅ |\n")
                else:
                    f.write(f"| {result['gamma']} | - | - | - | - | ❌ |\n")
            
            f.write(f"\n## Key Insights\n\n")
            
            if len(successful_results) >= 2:
                # Analyze gamma effect
                successful_results.sort(key=lambda x: x['gamma'])
                
                min_gamma = successful_results[0]['gamma']
                max_gamma = successful_results[-1]['gamma']
                min_violations = successful_results[0]['violations_count']
                max_violations = successful_results[-1]['violations_count']
                
                f.write(f"### Gamma Control Effect\n\n")
                f.write(f"- **Lowest Gamma ({min_gamma})**: {min_violations} violations\n")
                f.write(f"- **Highest Gamma ({max_gamma})**: {max_violations} violations\n")
                
                if min_violations > max_violations:
                    f.write(f"- **✅ Gamma Control Confirmed**: Higher gamma reduces violations\n")
                else:
                    f.write(f"- **⚠️ Gamma Effect Unclear**: Check experimental setup\n")
                
                # Calculate violation reduction
                total_reduction = min_violations - max_violations
                if min_violations > 0:
                    reduction_percent = (total_reduction / min_violations) * 100
                    f.write(f"- **Violation Reduction**: {total_reduction} violations ({reduction_percent:.1f}%)\n")
                
                f.write(f"\n### Control Knob Analysis\n\n")
                
                # Categorize gamma values
                low_gamma_results = [r for r in successful_results if r['gamma'] <= np.percentile([r['gamma'] for r in successful_results], 33)]
                medium_gamma_results = [r for r in successful_results if np.percentile([r['gamma'] for r in successful_results], 33) < r['gamma'] <= np.percentile([r['gamma'] for r in successful_results], 66)]
                high_gamma_results = [r for r in successful_results if r['gamma'] > np.percentile([r['gamma'] for r in successful_results], 66)]
                
                avg_low_violations = np.mean([r['violations_count'] for r in low_gamma_results]) if low_gamma_results else 0
                avg_medium_violations = np.mean([r['violations_count'] for r in medium_gamma_results]) if medium_gamma_results else 0
                avg_high_violations = np.mean([r['violations_count'] for r in high_gamma_results]) if high_gamma_results else 0
                
                f.write(f"- **Low Gamma**: Average {avg_low_violations:.1f} violations (system accepts violations for efficiency)\n")
                f.write(f"- **Medium Gamma**: Average {avg_medium_violations:.1f} violations (balanced approach)\n")
                f.write(f"- **High Gamma**: Average {avg_high_violations:.1f} violations (strict rule adherence)\n")
                
                f.write(f"\n## Conclusion\n\n")
                f.write(f"The penalty cost gamma demonstrates clear effectiveness as a 'control knob' for balancing:\n")
                f.write(f"- **Rule Adherence**: Higher gamma enforces stricter constraint compliance\n")
                f.write(f"- **Operational Efficiency**: Lower gamma allows flexibility for operational needs\n")
                f.write(f"- **System Design**: Gamma can be tuned based on specific operational requirements\n")
            
            else:
                f.write(f"Insufficient successful results for comprehensive analysis.\n")
        
        print(f"📋 Analysis report saved to: {report_file}")
    
    def create_visualization(self, experiment_name: str):
        """Create visualization charts showing gamma control effect."""
        successful_results = [r for r in self.results if r['status'] == 'success']
        
        if len(successful_results) < 2:
            print("❌ Insufficient data for visualization")
            return
        
        # Sort by gamma value
        successful_results.sort(key=lambda x: x['gamma'])
        
        gamma_values = [r['gamma'] for r in successful_results]
        violations = [r['violations_count'] for r in successful_results]
        penalty_costs = [r['total_penalty_cost'] for r in successful_results]
        
        # Create the main gamma control chart
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        fig.suptitle('Gamma Control Analysis: Penalty Cost as a Control Knob', fontsize=16, fontweight='bold')
        
        # Plot 1: Violations vs Gamma
        ax1.plot(gamma_values, violations, 'o-', linewidth=3, markersize=8, color='red', label='Violations')
        ax1.fill_between(gamma_values, violations, alpha=0.3, color='red')
        ax1.set_xlabel('Gamma (Penalty Cost)', fontsize=12)
        ax1.set_ylabel('Number of Violations', fontsize=12)
        ax1.set_title('Violation Count vs Gamma Value', fontsize=14, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # Add annotations for key insights
        if len(gamma_values) >= 3:
            low_idx = 0
            high_idx = -1
            
            ax1.annotate(f'Low γ: {violations[low_idx]} violations\n(System accepts violations)', 
                        xy=(gamma_values[low_idx], violations[low_idx]), 
                        xytext=(gamma_values[low_idx] + (max(gamma_values) - min(gamma_values)) * 0.1, violations[low_idx] + max(violations) * 0.1),
                        arrowprops=dict(arrowstyle='->', color='red', alpha=0.7),
                        bbox=dict(boxstyle="round,pad=0.3", facecolor='yellow', alpha=0.7),
                        fontsize=10)
            
            ax1.annotate(f'High γ: {violations[high_idx]} violations\n(Strict rule adherence)', 
                        xy=(gamma_values[high_idx], violations[high_idx]), 
                        xytext=(gamma_values[high_idx] - (max(gamma_values) - min(gamma_values)) * 0.1, violations[high_idx] + max(violations) * 0.1),
                        arrowprops=dict(arrowstyle='->', color='green', alpha=0.7),
                        bbox=dict(boxstyle="round,pad=0.3", facecolor='lightgreen', alpha=0.7),
                        fontsize=10)
        
        # Plot 2: Penalty Cost vs Gamma
        ax2.bar(gamma_values, penalty_costs, alpha=0.7, color='blue', label='Total Penalty Cost')
        ax2.set_xlabel('Gamma (Penalty Cost)', fontsize=12)
        ax2.set_ylabel('Total Penalty Cost Incurred', fontsize=12)
        ax2.set_title('Actual Penalty Cost vs Gamma Value', fontsize=14, fontweight='bold')
        ax2.grid(True, alpha=0.3)
        ax2.legend()
        
        plt.tight_layout()
        
        # Save the chart
        chart_file = f"{self.output_dir}/{experiment_name}_gamma_control_chart_{self.timestamp}.png"
        plt.savefig(chart_file, dpi=300, bbox_inches='tight')
        plt.savefig(chart_file.replace('.png', '.pdf'), bbox_inches='tight')  # Also save as PDF
        
        print(f"📊 Gamma control chart saved to: {chart_file}")
        
        # Create additional detailed analysis chart
        self.create_detailed_analysis_chart(experiment_name, successful_results)
        
        # Close the figure to save memory
        plt.close()
    
    def create_detailed_analysis_chart(self, experiment_name: str, results: List[Dict]):
        """Create detailed analysis chart with multiple metrics."""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Comprehensive Gamma Control Analysis', fontsize=16, fontweight='bold')
        
        gamma_values = [r['gamma'] for r in results]
        violations = [r['violations_count'] for r in results]
        violation_flow = [r['total_violation_flow'] for r in results]
        penalty_costs = [r['total_penalty_cost'] for r in results]
        sim_times = [r['simulation_time'] for r in results]
        
        # Plot 1: Violations and Flow
        ax1.plot(gamma_values, violations, 'o-', linewidth=2, markersize=6, color='red', label='Violation Count')
        ax1_twin = ax1.twinx()
        ax1_twin.plot(gamma_values, violation_flow, 's-', linewidth=2, markersize=6, color='orange', label='Violation Flow')
        ax1.set_xlabel('Gamma')
        ax1.set_ylabel('Violation Count', color='red')
        ax1_twin.set_ylabel('Violation Flow', color='orange')
        ax1.set_title('Violations and Flow vs Gamma')
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Penalty Cost Analysis
        ax2.bar(gamma_values, penalty_costs, alpha=0.7, color='purple')
        ax2.set_xlabel('Gamma')
        ax2.set_ylabel('Total Penalty Cost')
        ax2.set_title('Penalty Cost vs Gamma')
        ax2.grid(True, alpha=0.3)
        
        # Plot 3: Efficiency Analysis (Simulation Time)
        ax3.plot(gamma_values, sim_times, 'o-', linewidth=2, markersize=6, color='blue')
        ax3.set_xlabel('Gamma')
        ax3.set_ylabel('Simulation Time (seconds)')
        ax3.set_title('Computational Efficiency vs Gamma')
        ax3.grid(True, alpha=0.3)
        
        # Plot 4: Control Knob Effectiveness
        # Calculate effectiveness metric: (max_violations - current_violations) / max_violations
        max_violations = max(violations) if violations else 1
        effectiveness = [(max_violations - v) / max_violations * 100 for v in violations]
        
        ax4.fill_between(gamma_values, effectiveness, alpha=0.6, color='green')
        ax4.plot(gamma_values, effectiveness, 'o-', linewidth=2, markersize=6, color='darkgreen')
        ax4.set_xlabel('Gamma')
        ax4.set_ylabel('Control Effectiveness (%)')
        ax4.set_title('Gamma Control Effectiveness')
        ax4.grid(True, alpha=0.3)
        ax4.set_ylim(0, 100)
        
        plt.tight_layout()
        
        # Save detailed chart
        detailed_chart_file = f"{self.output_dir}/{experiment_name}_detailed_analysis_{self.timestamp}.png"
        plt.savefig(detailed_chart_file, dpi=300, bbox_inches='tight')
        
        print(f"📊 Detailed analysis chart saved to: {detailed_chart_file}")
        plt.close()
    
    def load_and_visualize_existing_results(self, results_file: str):
        """Load existing results and create visualizations."""
        try:
            with open(results_file, 'r') as f:
                data = json.load(f)
            
            self.results = data['results']
            experiment_name = data['experiment_name']
            
            print(f"📁 Loaded results from: {results_file}")
            print(f"Experiment: {experiment_name}")
            print(f"Results count: {len(self.results)}")
            
            self.create_visualization(experiment_name)
            
        except Exception as e:
            print(f"❌ Error loading results: {e}")

def create_simulation_runner():
    """
    Create a simulation runner function that integrates with the main system.
    """
    def simulation_runner(gamma_value):
        """
        Run simulation with specified gamma value.
        This function should:
        1. Set up restrictions with the specified gamma
        2. Run the simulation 
        3. Generate TSG.txt with escape edges
        """
        print(f"    Running simulation with gamma = {gamma_value}")
        
        # This is a placeholder - in real implementation, this would:
        # 1. Import and use RestrictionForTimeFrameController
        # 2. Set restrictions with specified gamma
        # 3. Run full simulation pipeline
        # 4. Generate TSG.txt
        
        # For now, we'll use existing TSG and simulate different outcomes
        # In production, integrate with main.py pipeline
        
        # Simulate different violation outcomes based on gamma
        # This is just for demonstration - replace with actual simulation
        pass
    
    return simulation_runner

if __name__ == "__main__":
    print("🎯 GAMMA CONTROL ANALYSIS TOOL")
    print("=" * 50)
    
    # Create analyzer
    analyzer = GammaAnalysisRunner()
    
    # Example gamma values to test - from low to high
    gamma_values = [1, 10, 50, 100, 200, 400, 800]
    
    print(f"This tool will analyze gamma control effectiveness across values: {gamma_values}")
    print()
    print("To run full analysis, integrate with your simulation pipeline.")
    print("For now, you can:")
    print("1. Load existing results with: analyzer.load_and_visualize_existing_results('path/to/results.json')")
    print("2. Or run: python run_gamma_analysis.py")
    
    # Create simulation runner
    sim_runner = create_simulation_runner()
    
    # Note: Uncomment below to run actual analysis
    # results = analyzer.run_gamma_experiment(gamma_values, sim_runner, "gamma_control_study")
