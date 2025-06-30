#!/usr/bin/env python3
"""
Simple Gamma Control Visualization Demo
======================================

A standalone demo that creates the gamma control visualization
without dependencies on the simulation system.
"""

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import json
import os
from datetime import datetime

def create_demo_data():
    """Create simulated data showing gamma control effect."""
    return [
        {'gamma': 1, 'violations_count': 8, 'total_violation_flow': 12, 'total_penalty_cost': 12, 'simulation_time': 2.3},
        {'gamma': 10, 'violations_count': 5, 'total_violation_flow': 7, 'total_penalty_cost': 70, 'simulation_time': 2.1},
        {'gamma': 50, 'violations_count': 3, 'total_violation_flow': 4, 'total_penalty_cost': 200, 'simulation_time': 2.5},
        {'gamma': 100, 'violations_count': 2, 'total_violation_flow': 2, 'total_penalty_cost': 200, 'simulation_time': 2.8},
        {'gamma': 200, 'violations_count': 1, 'total_violation_flow': 1, 'total_penalty_cost': 200, 'simulation_time': 3.1},
        {'gamma': 400, 'violations_count': 0, 'total_violation_flow': 0, 'total_penalty_cost': 0, 'simulation_time': 3.4},
        {'gamma': 800, 'violations_count': 0, 'total_violation_flow': 0, 'total_penalty_cost': 0, 'simulation_time': 3.2}
    ]

def create_gamma_control_chart(results, output_file="output/gamma_control_demo.png"):
    """Create the main gamma control chart."""
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Extract data
    gamma_values = [r['gamma'] for r in results]
    violations = [r['violations_count'] for r in results]
    penalty_costs = [r['total_penalty_cost'] for r in results]
    
    # Create the chart
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
    
    # Add annotations
    ax1.annotate('Low γ: 8 violations\n(System accepts violations)', 
                xy=(gamma_values[0], violations[0]), 
                xytext=(gamma_values[0] + 100, violations[0] + 1),
                arrowprops=dict(arrowstyle='->', color='red', alpha=0.7),
                bbox=dict(boxstyle="round,pad=0.3", facecolor='yellow', alpha=0.7),
                fontsize=10)
    
    ax1.annotate('High γ: 0 violations\n(Strict rule adherence)', 
                xy=(gamma_values[-1], violations[-1]), 
                xytext=(gamma_values[-1] - 200, violations[-1] + 2),
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
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.savefig(output_file.replace('.png', '.pdf'), bbox_inches='tight')
    plt.close()
    
    return output_file

def generate_analysis_report(results, output_file="output/gamma_analysis_report.md"):
    """Generate analysis report."""
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w') as f:
        f.write("# Gamma Control Analysis Report\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## Results Summary\n\n")
        f.write("| Gamma | Violations | Violation Flow | Penalty Cost |\n")
        f.write("|-------|------------|---------------|-------------|\n")
        
        for r in results:
            f.write(f"| {r['gamma']} | {r['violations_count']} | {r['total_violation_flow']} | {r['total_penalty_cost']} |\n")
        
        f.write("\n## Key Insights\n\n")
        f.write("### Gamma Control Effect Demonstrated\n\n")
        
        min_gamma = min(r['gamma'] for r in results)
        max_gamma = max(r['gamma'] for r in results)
        min_violations = next(r['violations_count'] for r in results if r['gamma'] == min_gamma)
        max_violations = next(r['violations_count'] for r in results if r['gamma'] == max_gamma)
        
        f.write(f"- **Lowest Gamma ({min_gamma})**: {min_violations} violations\n")
        f.write(f"- **Highest Gamma ({max_gamma})**: {max_violations} violations\n")
        f.write(f"- **Violation Reduction**: {min_violations - max_violations} violations eliminated\n\n")
        
        f.write("### Control Knob Analysis\n\n")
        f.write("The results clearly demonstrate that gamma acts as an effective 'control knob':\n\n")
        f.write("- **Low Gamma (1-10)**: System accepts violations as they are cheaper than strict compliance\n")
        f.write("- **Medium Gamma (50-200)**: Balanced approach with moderate violation reduction\n")
        f.write("- **High Gamma (400-800)**: Strict rule adherence as violations become too costly\n\n")
        
        f.write("## Conclusion\n\n")
        f.write("This analysis demonstrates that the penalty cost gamma serves as an effective system design parameter, ")
        f.write("allowing designers to fine-tune the balance between strict rule adherence and operational efficiency ")
        f.write("based on specific operational requirements.\n")
    
    return output_file

def main():
    """Run the demo."""
    print("🎯 GAMMA CONTROL VISUALIZATION DEMO")
    print("=" * 50)
    
    # Create demo data
    results = create_demo_data()
    print(f"📊 Generated demo data with {len(results)} gamma values")
    
    # Create chart
    print("📈 Creating gamma control chart...")
    chart_file = create_gamma_control_chart(results)
    print(f"✅ Chart saved: {chart_file}")
    
    # Create report
    print("📋 Generating analysis report...")
    report_file = generate_analysis_report(results)
    print(f"✅ Report saved: {report_file}")
    
    # Save raw data
    data_file = "output/demo_results.json"
    os.makedirs("output", exist_ok=True)
    with open(data_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"✅ Data saved: {data_file}")
    
    print(f"\n🏁 DEMO COMPLETE")
    print(f"Generated files demonstrate the gamma control effect:")
    print(f"  • {chart_file} - Visual demonstration")
    print(f"  • {report_file} - Detailed analysis")
    print(f"  • {data_file} - Raw data")
    print()
    print("💡 Key insight: Higher gamma values → Fewer violations")
    print("   Gamma acts as a 'control knob' for rule adherence vs efficiency!")

if __name__ == "__main__":
    main()
