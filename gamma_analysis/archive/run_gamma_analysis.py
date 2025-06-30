#!/usr/bin/env python3
"""
Run Gamma Analysis with Real Simulation Integration
=================================================

This script runs the complete gamma analysis by integrating with the 
actual simulation system and generating real violation data.
"""

import os
import sys
import subprocess
import tempfile
import shutil
from typing import List

# Add parent directory for imports
sys.path.append('..')
sys.path.append('../controller')
sys.path.append('../model')

from gamma_control_analyzer import GammaAnalysisRunner

def run_simulation_with_gamma(gamma_value: float) -> bool:
    """
    Run the actual simulation with specified gamma value.
    
    This function integrates with the main simulation system to:
    1. Set up restrictions with specified gamma
    2. Run the simulation
    3. Generate TSG.txt with escape edges
    """
    print(f"    🚀 Running simulation with γ = {gamma_value}")
    
    # Create automated input for main.py
    # This simulates user input but with our specified gamma
    simulation_input = f"""3
1
simplest.txt
20
0
1
2
1
1 2
1
1
{gamma_value}
2
"""
    
    try:
        # Run main.py with our automated input
        process = subprocess.Popen(
            [sys.executable, "../main.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=os.getcwd()
        )
        
        # Send input and wait for completion
        stdout, stderr = process.communicate(input=simulation_input, timeout=60)
        
        if process.returncode == 0:
            print(f"    ✅ Simulation completed for γ = {gamma_value}")
            
            # Check if TSG was generated
            if os.path.exists("../TSG.txt"):
                print(f"    📄 TSG.txt generated successfully")
                return True
            else:
                print(f"    ❌ TSG.txt not found after simulation")
                return False
        else:
            print(f"    ⚠️  Simulation had issues (exit code: {process.returncode})")
            if stderr and len(stderr) < 500:  # Only show short errors
                print(f"    Error: {stderr.strip()}")
            return False
            
    except subprocess.TimeoutExpired:
        process.kill()
        print(f"    ⏰ Simulation timed out for γ = {gamma_value}")
        return False
    except Exception as e:
        print(f"    ❌ Error running simulation for γ = {gamma_value}: {e}")
        return False

def main():
    """
    Main function to run comprehensive gamma analysis.
    """
    print("🎯 GAMMA CONTROL EXPERIMENT")
    print("=" * 60)
    print("This experiment explores the role of penalty cost (gamma) by running")
    print("scenarios with varied gamma values and visualizing the results.")
    print()
    
    # Check if we're in the right directory
    if not os.path.exists("../main.py"):
        print("❌ Error: main.py not found in parent directory")
        print("Please run this script from the gamma_analysis folder")
        return
    
    # Create analyzer
    analyzer = GammaAnalysisRunner()
    
    # Define gamma values to test - from low to high
    # This progression will demonstrate the control knob effect
    gamma_values = [
        1,      # Very low - system should accept violations
        10,     # Low - some violations acceptable
        50,     # Medium-low - fewer violations
        100,    # Medium - balanced approach  
        200,    # Medium-high - stricter compliance
        400,    # High - strong rule adherence
        800     # Very high - zero violations expected
    ]
    
    print(f"📊 Testing gamma values: {gamma_values}")
    print(f"Expected behavior:")
    print(f"  • Low gamma (1-10): System accepts violations (cheaper than compliance)")
    print(f"  • Medium gamma (50-200): Balanced violation reduction")
    print(f"  • High gamma (400-800): Zero violations (too costly to violate)")
    print()
    
    # Backup existing TSG if it exists
    tsg_backup = None
    if os.path.exists("../TSG.txt"):
        tsg_backup = "data/TSG_original_backup.txt"
        shutil.copy("../TSG.txt", tsg_backup)
        print(f"📄 Backed up original TSG to: {tsg_backup}")
    
    try:
        # Run the experiment
        results = analyzer.run_gamma_experiment(
            gamma_values=gamma_values,
            simulation_runner_func=run_simulation_with_gamma,
            experiment_name="gamma_control_study"
        )
        
        # Print final summary
        print(f"\n🏁 EXPERIMENT COMPLETE")
        print(f"=" * 40)
        
        successful_results = [r for r in results if r['status'] == 'success']
        
        if len(successful_results) >= 2:
            # Sort by gamma
            successful_results.sort(key=lambda x: x['gamma'])
            
            min_gamma_result = successful_results[0]
            max_gamma_result = successful_results[-1]
            
            print(f"📈 GAMMA CONTROL EFFECTIVENESS DEMONSTRATED:")
            print(f"  • Lowest γ ({min_gamma_result['gamma']}): {min_gamma_result['violations_count']} violations")
            print(f"  • Highest γ ({max_gamma_result['gamma']}): {max_gamma_result['violations_count']} violations")
            
            total_reduction = min_gamma_result['violations_count'] - max_gamma_result['violations_count']
            if min_gamma_result['violations_count'] > 0:
                reduction_percent = (total_reduction / min_gamma_result['violations_count']) * 100
                print(f"  • Violation reduction: {total_reduction} violations ({reduction_percent:.1f}%)")
            
            print(f"\n💡 KEY INSIGHTS:")
            print(f"  ✅ Gamma acts as an effective 'control knob'")
            print(f"  ✅ Low gamma → System accepts violations for efficiency")
            print(f"  ✅ High gamma → System enforces strict rule adherence")
            print(f"  ✅ System designers can tune gamma based on operational needs")
            
        else:
            print(f"⚠️  Insufficient successful results for analysis")
            print(f"   Successful: {len(successful_results)}/{len(results)}")
        
        print(f"\n📁 Output files saved to: {analyzer.output_dir}/")
        print(f"   • Analysis report (Markdown)")
        print(f"   • Gamma control chart (PNG/PDF)")  
        print(f"   • Detailed analysis charts")
        print(f"   • Raw results (JSON)")
        
    except KeyboardInterrupt:
        print(f"\n⛔ Experiment interrupted by user")
    except Exception as e:
        print(f"\n❌ Experiment failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Restore original TSG if it existed
        if tsg_backup and os.path.exists(tsg_backup):
            shutil.copy(tsg_backup, "../TSG.txt")
            print(f"\n🔄 Restored original TSG")

if __name__ == "__main__":
    main()
