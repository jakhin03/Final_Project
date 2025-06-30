#!/usr/bin/env python3
"""
Cleanup and Organization Script

This script cleans up the gamma_analysis folder and demonstrates
the new organized structure.
"""

import os
import shutil
from utils import organize_files_by_type, cleanup_empty_directories, print_directory_summary

def main():
    """Run cleanup and organization"""
    
    print("🧹 CLEANING UP GAMMA ANALYSIS FOLDER")
    print("=" * 40)
    
    base_dir = os.path.dirname(__file__)
    output_dir = os.path.join(base_dir, 'output')
    
    # Define organized structure
    target_structure = {
        'charts': os.path.join(output_dir, 'charts'),
        'reports': os.path.join(output_dir, 'reports'),
        'data': os.path.join(output_dir, 'data'),
        'sessions': os.path.join(output_dir, 'sessions'),
        'experiments': os.path.join(output_dir, 'experiments')
    }
    
    # Create directories
    for dir_path in target_structure.values():
        os.makedirs(dir_path, exist_ok=True)
    
    # Organize existing files
    print("📁 Organizing files by type...")
    moved_files = organize_files_by_type(output_dir, target_structure)
    
    for file_type, files in moved_files.items():
        if files:
            print(f"   {file_type}: {len(files)} files organized")
    
    # Clean up empty directories
    cleanup_empty_directories(output_dir)
    
    print("\n📊 ORGANIZED OUTPUT STRUCTURE")
    print("=" * 32)
    
    # Print summary of each directory
    for name, path in target_structure.items():
        print_directory_summary(path, name.title())
    
    print("\n✅ Cleanup completed!")
    print(f"📂 Organized output directory: {output_dir}")
    
    print("\n🚀 READY TO USE")
    print("=" * 15)
    print("Run: python gamma_analysis.py --demo")
    print("Or:  python gamma_analysis.py")

if __name__ == "__main__":
    main()
