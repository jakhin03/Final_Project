#!/usr/bin/env python3
"""
Gamma Control Analysis Suite - Main Script

This is the primary script for running gamma control analysis experiments.
It provides a clean, organized interface for all gamma control functionality.

Usage:
    python gamma_analysis.py [options]
    
Options:
    --demo                  Run demonstration with simulated data
    --config CONFIG_FILE    Use specific configuration file
    --gamma-values X,Y,Z    Test specific gamma values
    --output-dir DIR        Specify output directory
    --help                  Show this help message
"""

import os
import sys
import argparse
import json
from datetime import datetime
from typing import List, Dict, Optional

# Add parent directory for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config_loader import load_config
from gamma_control_analyzer import GammaControlAnalyzer

def create_organized_output_structure(base_dir: str) -> Dict[str, str]:
    """Create organized output directory structure"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    directories = {
        'base': base_dir,
        'experiment': os.path.join(base_dir, 'experiments', f'experiment_{timestamp}'),
        'charts': os.path.join(base_dir, 'charts'),
        'reports': os.path.join(base_dir, 'reports'),
        'data': os.path.join(base_dir, 'data'),
        'sessions': os.path.join(base_dir, 'sessions')
    }
    
    # Create all directories
    for dir_path in directories.values():
        os.makedirs(dir_path, exist_ok=True)
    
    return directories

def run_demo_analysis(config, output_dirs: Dict[str, str]):
    """Run demonstration analysis with simulated data"""
    
    print("🎯 RUNNING GAMMA CONTROL DEMONSTRATION")
    print("=" * 45)
    
    # Use configurable gamma analysis for demo
    from configurable_gamma_analysis import generate_configurable_analysis, create_flow_analysis_chart, create_detailed_report
    
    # Generate analysis data
    results = generate_configurable_analysis(config)
    
    # Create charts
    chart_file = create_flow_analysis_chart(results, config)
    
    # Move chart to organized location
    if os.path.exists(chart_file):
        dest_chart = os.path.join(output_dirs['charts'], f"demo_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        os.rename(chart_file, dest_chart)
        print(f"📊 Chart saved: {dest_chart}")
    
    # Create report
    report_file = create_detailed_report(results, config)
    
    # Move report to organized location
    if os.path.exists(report_file):
        dest_report = os.path.join(output_dirs['reports'], f"demo_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        os.rename(report_file, dest_report)
        print(f"📄 Report saved: {dest_report}")
    
    return results

def run_comprehensive_analysis(config, output_dirs: Dict[str, str], gamma_values: Optional[List[float]] = None):
    """Run comprehensive gamma analysis"""
    
    print("🔬 RUNNING COMPREHENSIVE GAMMA ANALYSIS")
    print("=" * 42)
    
    # Initialize analyzer with organized output
    analyzer = GammaControlAnalyzer(output_dirs['experiment'])
    
    # Use config gamma values if not specified
    if gamma_values is None:
        gamma_values = config.get_gamma_values()
    
    # Run complete analysis
    outputs = analyzer.run_complete_analysis(
        gamma_values=gamma_values,
        num_runs_per_gamma=config.get_num_runs_per_gamma()
    )
    
    print(f"\n📂 Results saved to: {outputs['experiment_dir']}")
    return outputs

def cleanup_old_files(output_dir: str, keep_recent: int = 5):
    """Clean up old experiment files, keeping only recent ones"""
    
    experiments_dir = os.path.join(output_dir, 'experiments')
    if not os.path.exists(experiments_dir):
        return
    
    # Get all experiment directories
    experiment_dirs = [d for d in os.listdir(experiments_dir) 
                      if os.path.isdir(os.path.join(experiments_dir, d)) and d.startswith('experiment_')]
    
    # Sort by modification time (newest first)
    experiment_dirs.sort(key=lambda x: os.path.getmtime(os.path.join(experiments_dir, x)), reverse=True)
    
    # Remove old experiments
    if len(experiment_dirs) > keep_recent:
        for old_exp in experiment_dirs[keep_recent:]:
            old_path = os.path.join(experiments_dir, old_exp)
            import shutil
            shutil.rmtree(old_path)
            print(f"🗑️  Removed old experiment: {old_exp}")

def print_summary(output_dirs: Dict[str, str]):
    """Print summary of organized output structure"""
    
    print("\n" + "=" * 60)
    print("📁 ORGANIZED OUTPUT STRUCTURE")
    print("=" * 60)
    
    structure_info = [
        ("Base Directory", output_dirs['base'], "Main output directory"),
        ("Charts", output_dirs['charts'], "Visualization files (.png, .pdf)"),
        ("Reports", output_dirs['reports'], "Analysis reports (.txt, .md)"),
        ("Data", output_dirs['data'], "Raw data files (.csv, .json)"),
        ("Sessions", output_dirs['sessions'], "Session summaries"),
        ("Experiments", output_dirs.get('experiment', ''), "Individual experiment results")
    ]
    
    for name, path, description in structure_info:
        if path and os.path.exists(path):
            file_count = len([f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))])
            print(f"📂 {name:<15} {path}")
            print(f"   └─ {description} ({file_count} files)")
        else:
            print(f"📂 {name:<15} (not created)")

def main():
    """Main entry point"""
    
    parser = argparse.ArgumentParser(description="Gamma Control Analysis Suite")
    parser.add_argument('--demo', action='store_true', help='Run demonstration analysis')
    parser.add_argument('--config', default='config.json', help='Configuration file')
    parser.add_argument('--gamma-values', help='Comma-separated gamma values to test')
    parser.add_argument('--output-dir', default='output', help='Output directory')
    parser.add_argument('--cleanup', action='store_true', help='Clean up old files')
    
    args = parser.parse_args()
    
    print("🧪 GAMMA CONTROL ANALYSIS SUITE")
    print("=" * 35)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load configuration
    config = load_config(args.config)
    if args.output_dir != 'output':
        config.update_config({'output_settings': {'output_directory': args.output_dir}})
    
    # Create organized output structure
    output_dirs = create_organized_output_structure(config.get_output_directory())
    
    # Parse gamma values if provided
    gamma_values = None
    if args.gamma_values:
        try:
            gamma_values = [float(x.strip()) for x in args.gamma_values.split(',')]
            print(f"🎛️  Using custom gamma values: {gamma_values}")
        except ValueError:
            print("❌ Invalid gamma values format. Using config defaults.")
    
    # Run analysis
    try:
        if args.demo:
            results = run_demo_analysis(config, output_dirs)
        else:
            results = run_comprehensive_analysis(config, output_dirs, gamma_values)
        
        # Cleanup old files if requested
        if args.cleanup:
            cleanup_old_files(config.get_output_directory())
        
        # Print summary
        print_summary(output_dirs)
        
        print("\n✅ Analysis completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Analysis failed: {e}")
        if config.is_debug_mode():
            import traceback
            traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
