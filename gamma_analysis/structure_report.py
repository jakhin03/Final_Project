#!/usr/bin/env python3
"""
Generate Structure Report for Cleaned Gamma Analysis Folder
=========================================================

This script generates a comprehensive report of the cleaned and organized
gamma analysis folder structure.
"""

import os
from pathlib import Path

def generate_structure_report():
    """Generate a detailed structure report."""
    
    base_dir = "/home/ubuntu/project/pps-game/server/core/gamma_analysis"
    
    print("📊 GAMMA ANALYSIS FOLDER - FINAL CLEAN STRUCTURE")
    print("=" * 60)
    
    # Core scripts
    print("\n🎯 CORE ANALYSIS SCRIPTS")
    print("-" * 25)
    core_scripts = [
        ("gamma_analysis.py", "Main analysis entry point"),
        ("gamma_control_analyzer.py", "Core analysis and visualization engine"),
        ("configurable_gamma_analysis.py", "Configurable analysis with flow explanation"),
        ("violation_analyzer.py", "Escape edge violation detection")
    ]
    
    for script, description in core_scripts:
        if os.path.exists(os.path.join(base_dir, script)):
            print(f"  ✅ {script:<30} - {description}")
        else:
            print(f"  ❌ {script:<30} - MISSING")
    
    # Integration utilities
    print("\n🔧 INTEGRATION & UTILITIES")
    print("-" * 30)
    util_scripts = [
        ("integrated_gamma_control.py", "Gamma control integration utilities"),
        ("config_loader.py", "Configuration management"),
        ("utils.py", "Common utilities and helpers"),
        ("simple_gamma_test.py", "Simple testing utilities")
    ]
    
    for script, description in util_scripts:
        if os.path.exists(os.path.join(base_dir, script)):
            print(f"  ✅ {script:<30} - {description}")
        else:
            print(f"  ❌ {script:<30} - MISSING")
    
    # Configuration files
    print("\n⚙️ CONFIGURATION FILES")
    print("-" * 25)
    config_files = [
        ("config.json", "Full configuration options"),
        ("simple_config.json", "Basic configuration for quick tests")
    ]
    
    for config_file, description in config_files:
        if os.path.exists(os.path.join(base_dir, config_file)):
            print(f"  ✅ {config_file:<30} - {description}")
        else:
            print(f"  ❌ {config_file:<30} - MISSING")
    
    # Documentation
    print("\n📖 DOCUMENTATION")
    print("-" * 20)
    doc_files = [
        ("README.md", "Main documentation and usage guide"),
        ("FLOW_EXPLANATION.md", "Detailed flow value explanation"),
        ("FINAL_ANALYSIS_SUMMARY.md", "Analysis summary and results"),
        ("CLEANUP_SUMMARY.md", "Cleanup actions performed")
    ]
    
    for doc_file, description in doc_files:
        if os.path.exists(os.path.join(base_dir, doc_file)):
            print(f"  ✅ {doc_file:<30} - {description}")
        else:
            print(f"  ❌ {doc_file:<30} - MISSING")
    
    # Output structure
    print("\n📁 OUTPUT STRUCTURE")
    print("-" * 20)
    
    output_dir = os.path.join(base_dir, "output")
    if os.path.exists(output_dir):
        for item in sorted(os.listdir(output_dir)):
            item_path = os.path.join(output_dir, item)
            if os.path.isdir(item_path):
                print(f"  📂 {item}/")
                # Show subdirectories
                for subitem in sorted(os.listdir(item_path)):
                    subitem_path = os.path.join(item_path, subitem)
                    if os.path.isdir(subitem_path):
                        file_count = len([f for f in os.listdir(subitem_path) if f != "README.md"])
                        print(f"    📂 {subitem}/ ({file_count} files)")
    
    # Archive
    print("\n🗂️ ARCHIVED FILES")
    print("-" * 20)
    
    archive_dir = os.path.join(base_dir, "archive")
    if os.path.exists(archive_dir):
        for item in sorted(os.listdir(archive_dir)):
            print(f"  📦 {item}")
    else:
        print("  No archived files")
    
    # Summary statistics
    print("\n📊 SUMMARY STATISTICS")
    print("-" * 25)
    
    # Count files
    total_files = 0
    total_dirs = 0
    
    for root, dirs, files in os.walk(base_dir):
        total_dirs += len(dirs)
        total_files += len(files)
    
    print(f"  📁 Total directories: {total_dirs}")
    print(f"  📄 Total files: {total_files}")
    
    # Count by category
    charts_count = 0
    reports_count = 0
    data_count = 0
    
    charts_dir = os.path.join(base_dir, "output", "charts")
    if os.path.exists(charts_dir):
        for root, dirs, files in os.walk(charts_dir):
            charts_count += len([f for f in files if f.endswith(('.png', '.pdf'))])
    
    reports_dir = os.path.join(base_dir, "output", "reports")
    if os.path.exists(reports_dir):
        for root, dirs, files in os.walk(reports_dir):
            reports_count += len([f for f in files if f.endswith(('.md', '.txt'))])
    
    data_dir = os.path.join(base_dir, "output", "data")
    if os.path.exists(data_dir):
        for root, dirs, files in os.walk(data_dir):
            data_count += len([f for f in files if f.endswith(('.csv', '.json'))])
    
    print(f"  📊 Charts: {charts_count}")
    print(f"  📋 Reports: {reports_count}")
    print(f"  📈 Data files: {data_count}")
    
    print("\n✨ CLEANUP SUCCESS!")
    print("=" * 25)
    print("  🧹 Old files removed or archived")
    print("  📁 Output structure reorganized")
    print("  📚 Documentation updated")
    print("  🎯 Core functionality preserved")

if __name__ == "__main__":
    generate_structure_report()
