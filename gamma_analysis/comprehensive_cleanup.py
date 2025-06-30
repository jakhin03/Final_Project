#!/usr/bin/env python3
"""
Comprehensive Cleanup and Reorganization Script
==============================================

This script cleans up old unnecessary files and reorganizes the gamma_analysis
folder and output structure for better organization and maintainability.
"""

import os
import shutil
import glob
from datetime import datetime
from pathlib import Path

class GammaAnalysisCleanup:
    """Handles cleanup and reorganization of gamma analysis files."""
    
    def __init__(self):
        self.base_dir = "/home/ubuntu/project/pps-game/server/core"
        self.gamma_dir = os.path.join(self.base_dir, "gamma_analysis")
        self.output_dir = os.path.join(self.gamma_dir, "output")
        self.cleanup_log = []
        
    def log_action(self, action: str):
        """Log cleanup actions."""
        self.cleanup_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] {action}")
        print(f"✅ {action}")
        
    def remove_old_files_from_main_directory(self):
        """Remove old gamma experiment files from main directory."""
        print("\n🧹 CLEANING UP OLD FILES FROM MAIN DIRECTORY")
        print("-" * 50)
        
        old_files = [
            "quick_gamma_test.py",
            "real_gamma_experiment.py", 
            "gamma_demo.py",
            "escape_edge_experiment.py",
            "test_gamma_integration.py"
        ]
        
        for filename in old_files:
            filepath = os.path.join(self.base_dir, filename)
            if os.path.exists(filepath):
                os.remove(filepath)
                self.log_action(f"Removed old file: {filename}")
                
    def consolidate_redundant_scripts(self):
        """Consolidate redundant or outdated analysis scripts."""
        print("\n🔄 CONSOLIDATING REDUNDANT SCRIPTS")
        print("-" * 40)
        
        # Files that can be removed as they're redundant or outdated
        redundant_files = [
            "complete_gamma_integration.py",  # Functionality covered by gamma_analysis.py
            "run_gamma_analysis.py",          # Functionality covered by gamma_analysis.py
            "simple_demo.py",                 # Can be removed, functionality in main scripts
            "gamma_evaluation_explanation.py" # This can be moved to docs if needed
        ]
        
        for filename in redundant_files:
            filepath = os.path.join(self.gamma_dir, filename)
            if os.path.exists(filepath):
                # Create backup before removal
                backup_dir = os.path.join(self.gamma_dir, "archive")
                os.makedirs(backup_dir, exist_ok=True)
                shutil.move(filepath, os.path.join(backup_dir, filename))
                self.log_action(f"Archived redundant script: {filename}")
                
    def reorganize_output_structure(self):
        """Reorganize output folder with better structure."""
        print("\n📁 REORGANIZING OUTPUT STRUCTURE")
        print("-" * 35)
        
        # Create improved folder structure
        new_structure = {
            "charts": {
                "analysis": "Analysis charts and plots",
                "comparison": "Comparison and trend charts", 
                "demo": "Demo and presentation charts"
            },
            "reports": {
                "analysis": "Detailed analysis reports",
                "summary": "Executive summary reports",
                "technical": "Technical documentation"
            },
            "data": {
                "raw": "Raw experiment data",
                "processed": "Processed analysis data",
                "exports": "Data exports and backups"
            },
            "experiments": {
                "sessions": "Individual session results",
                "batch": "Batch experiment results",
                "archived": "Archived experiment data"
            }
        }
        
        # Create the new structure
        for main_folder, subfolders in new_structure.items():
            main_path = os.path.join(self.output_dir, main_folder)
            os.makedirs(main_path, exist_ok=True)
            
            for subfolder, description in subfolders.items():
                subfolder_path = os.path.join(main_path, subfolder)
                os.makedirs(subfolder_path, exist_ok=True)
                
                # Create README in each subfolder
                readme_path = os.path.join(subfolder_path, "README.md")
                with open(readme_path, 'w') as f:
                    f.write(f"# {subfolder.title()}\n\n{description}\n")
                    
        self.log_action("Created improved output folder structure")
        
    def organize_existing_output_files(self):
        """Move existing output files to appropriate folders."""
        print("\n📋 ORGANIZING EXISTING OUTPUT FILES")
        print("-" * 40)
        
        # Organize charts
        charts_dir = os.path.join(self.output_dir, "charts")
        for chart_file in glob.glob(os.path.join(charts_dir, "*.png")) + glob.glob(os.path.join(charts_dir, "*.pdf")):
            filename = os.path.basename(chart_file)
            
            if "demo" in filename.lower():
                target_dir = os.path.join(charts_dir, "demo")
            elif "comparison" in filename.lower() or "trend" in filename.lower():
                target_dir = os.path.join(charts_dir, "comparison")
            else:
                target_dir = os.path.join(charts_dir, "analysis")
                
            if not os.path.exists(os.path.join(target_dir, filename)):
                shutil.move(chart_file, target_dir)
                self.log_action(f"Moved chart: {filename} → {os.path.basename(target_dir)}/")
                
        # Organize reports
        reports_dir = os.path.join(self.output_dir, "reports")
        for report_file in glob.glob(os.path.join(reports_dir, "*.md")) + glob.glob(os.path.join(reports_dir, "*.txt")):
            filename = os.path.basename(report_file)
            
            if "summary" in filename.lower():
                target_dir = os.path.join(reports_dir, "summary")
            elif "technical" in filename.lower() or "detail" in filename.lower():
                target_dir = os.path.join(reports_dir, "technical")
            else:
                target_dir = os.path.join(reports_dir, "analysis")
                
            if not os.path.exists(os.path.join(target_dir, filename)):
                shutil.move(report_file, target_dir)
                self.log_action(f"Moved report: {filename} → {os.path.basename(target_dir)}/")
                
        # Organize data files
        data_dir = os.path.join(self.output_dir, "data")
        for data_file in glob.glob(os.path.join(data_dir, "*.csv")) + glob.glob(os.path.join(data_dir, "*.json")):
            filename = os.path.basename(data_file)
            
            if "processed" in filename.lower() or "analysis" in filename.lower():
                target_dir = os.path.join(data_dir, "processed")
            elif "export" in filename.lower() or "backup" in filename.lower():
                target_dir = os.path.join(data_dir, "exports")
            else:
                target_dir = os.path.join(data_dir, "raw")
                
            if not os.path.exists(os.path.join(target_dir, filename)):
                shutil.move(data_file, target_dir)
                self.log_action(f"Moved data: {filename} → {os.path.basename(target_dir)}/")
                
    def clean_pycache_and_temp_files(self):
        """Remove Python cache and temporary files."""
        print("\n🗑️  CLEANING CACHE AND TEMPORARY FILES")
        print("-" * 45)
        
        # Remove __pycache__ directories
        for pycache_dir in glob.glob(os.path.join(self.gamma_dir, "**/__pycache__"), recursive=True):
            shutil.rmtree(pycache_dir)
            self.log_action(f"Removed cache directory: {os.path.relpath(pycache_dir, self.gamma_dir)}")
            
        # Remove temporary files
        temp_patterns = ["*.tmp", "*.temp", "*~", ".DS_Store", "Thumbs.db"]
        for pattern in temp_patterns:
            for temp_file in glob.glob(os.path.join(self.gamma_dir, "**", pattern), recursive=True):
                os.remove(temp_file)
                self.log_action(f"Removed temporary file: {os.path.basename(temp_file)}")
                
    def update_readme_with_new_structure(self):
        """Update README.md to reflect the new organization."""
        print("\n📝 UPDATING README WITH NEW STRUCTURE")
        print("-" * 42)
        
        readme_path = os.path.join(self.gamma_dir, "README.md")
        
        # Read current README
        with open(readme_path, 'r') as f:
            content = f.read()
            
        # Update the files structure section
        new_structure_text = """
```
gamma_analysis/
├── 📊 Core Analysis Scripts
│   ├── gamma_analysis.py            # Main analysis script (primary entry point)
│   ├── gamma_control_analyzer.py    # Core analysis and visualization engine
│   ├── configurable_gamma_analysis.py # Configurable analysis with flow explanation
│   └── violation_analyzer.py        # Escape edge violation detection
├── 🔧 Integration & Utilities  
│   ├── integrated_gamma_control.py  # Gamma control integration utilities
│   ├── config_loader.py            # Configuration management
│   ├── utils.py                    # Common utilities and helpers
│   └── simple_gamma_test.py        # Simple testing utilities
├── ⚙️ Configuration
│   ├── config.json                 # Full configuration options
│   └── simple_config.json          # Basic configuration for quick tests
├── 📁 Data & Results
│   ├── data/                       # Experiment data and TSG backups
│   └── output/                     # Organized analysis results
│       ├── charts/                 # Visualization files
│       │   ├── analysis/           # Analysis charts and plots
│       │   ├── comparison/         # Comparison and trend charts
│       │   └── demo/               # Demo and presentation charts
│       ├── reports/                # Analysis reports
│       │   ├── analysis/           # Detailed analysis reports
│       │   ├── summary/            # Executive summary reports
│       │   └── technical/          # Technical documentation
│       ├── data/                   # Raw and processed data
│       │   ├── raw/                # Raw experiment data
│       │   ├── processed/          # Processed analysis data
│       │   └── exports/            # Data exports and backups
│       └── experiments/            # Experiment organization
│           ├── sessions/           # Individual session results
│           ├── batch/              # Batch experiment results
│           └── archived/           # Archived experiment data
├── 🗂️ Archive
│   └── archive/                    # Archived redundant files
└── 📖 Documentation
    ├── README.md                   # This file
    ├── FLOW_EXPLANATION.md         # Detailed flow value explanation
    └── FINAL_ANALYSIS_SUMMARY.md   # Analysis summary and results
```"""
        
        # Replace the old structure
        import re
        pattern = r'```[\s\S]*?```'
        matches = re.findall(pattern, content)
        if matches:
            # Replace the first code block (which should be the structure)
            content = content.replace(matches[0], new_structure_text, 1)
            
            with open(readme_path, 'w') as f:
                f.write(content)
                
            self.log_action("Updated README.md with new structure")
            
    def create_cleanup_summary(self):
        """Create a summary of all cleanup actions."""
        print("\n📊 CREATING CLEANUP SUMMARY")
        print("-" * 32)
        
        summary_path = os.path.join(self.gamma_dir, "CLEANUP_SUMMARY.md")
        
        with open(summary_path, 'w') as f:
            f.write(f"# Gamma Analysis Cleanup Summary\n\n")
            f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"## Actions Performed\n\n")
            
            for i, action in enumerate(self.cleanup_log, 1):
                f.write(f"{i}. {action.split('] ')[1]}\n")
                
            f.write(f"\n## Summary\n\n")
            f.write(f"- **Total actions:** {len(self.cleanup_log)}\n")
            f.write(f"- **Files organized:** Multiple\n")
            f.write(f"- **Structure improved:** ✅\n")
            f.write(f"- **Redundancy reduced:** ✅\n")
            f.write(f"- **Documentation updated:** ✅\n")
            
        self.log_action(f"Created cleanup summary: CLEANUP_SUMMARY.md")
        
    def run_comprehensive_cleanup(self):
        """Run the complete cleanup and reorganization process."""
        print("🚀 STARTING COMPREHENSIVE GAMMA ANALYSIS CLEANUP")
        print("=" * 60)
        
        self.remove_old_files_from_main_directory()
        self.consolidate_redundant_scripts()
        self.reorganize_output_structure()
        self.organize_existing_output_files()
        self.clean_pycache_and_temp_files()
        self.update_readme_with_new_structure()
        self.create_cleanup_summary()
        
        print(f"\n✨ CLEANUP COMPLETED!")
        print("=" * 30)
        print(f"📝 Total actions performed: {len(self.cleanup_log)}")
        print(f"📁 Output structure reorganized")
        print(f"🗂️ Redundant files archived")
        print(f"📚 Documentation updated")
        print(f"📊 Summary created: CLEANUP_SUMMARY.md")

if __name__ == "__main__":
    cleanup = GammaAnalysisCleanup()
    cleanup.run_comprehensive_cleanup()
