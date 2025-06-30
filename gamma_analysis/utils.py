#!/usr/bin/env python3
"""
Gamma Analysis Utilities

Common utilities and helper functions for gamma control analysis.
"""

import os
import json
import shutil
from datetime import datetime
from typing import Dict, List, Any, Optional

def create_timestamped_directory(base_dir: str, prefix: str = "experiment") -> str:
    """Create a timestamped directory"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dir_path = os.path.join(base_dir, f"{prefix}_{timestamp}")
    os.makedirs(dir_path, exist_ok=True)
    return dir_path

def save_json_data(data: Dict[str, Any], file_path: str) -> None:
    """Save data to JSON file"""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2, default=str)

def load_json_data(file_path: str) -> Optional[Dict[str, Any]]:
    """Load data from JSON file"""
    if not os.path.exists(file_path):
        return None
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception:
        return None

def organize_files_by_type(source_dir: str, target_structure: Dict[str, str]) -> Dict[str, List[str]]:
    """Organize files by type into target directory structure"""
    
    moved_files = {key: [] for key in target_structure.keys()}
    
    if not os.path.exists(source_dir):
        return moved_files
    
    # File type mappings
    file_mappings = {
        'charts': ['.png', '.pdf', '.svg', '.jpg'],
        'reports': ['.txt', '.md', '.html'],
        'data': ['.csv', '.json', '.xlsx'],
        'logs': ['.log'],
        'configs': ['.json', '.yaml', '.yml']
    }
    
    for file_name in os.listdir(source_dir):
        file_path = os.path.join(source_dir, file_name)
        
        if os.path.isfile(file_path):
            file_ext = os.path.splitext(file_name)[1].lower()
            
            # Determine target directory
            target_key = None
            for key, extensions in file_mappings.items():
                if file_ext in extensions and key in target_structure:
                    target_key = key
                    break
            
            if target_key:
                target_dir = target_structure[target_key]
                os.makedirs(target_dir, exist_ok=True)
                
                target_path = os.path.join(target_dir, file_name)
                shutil.move(file_path, target_path)
                moved_files[target_key].append(target_path)
    
    return moved_files

def cleanup_empty_directories(base_dir: str) -> None:
    """Remove empty directories"""
    for root, dirs, files in os.walk(base_dir, topdown=False):
        for directory in dirs:
            dir_path = os.path.join(root, directory)
            try:
                if not os.listdir(dir_path):
                    os.rmdir(dir_path)
            except OSError:
                pass

def get_file_summary(directory: str) -> Dict[str, int]:
    """Get summary of files in directory"""
    summary = {'total_files': 0, 'total_size': 0, 'by_extension': {}}
    
    if not os.path.exists(directory):
        return summary
    
    for root, dirs, files in os.walk(directory):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            if os.path.isfile(file_path):
                summary['total_files'] += 1
                
                try:
                    file_size = os.path.getsize(file_path)
                    summary['total_size'] += file_size
                except OSError:
                    pass
                
                ext = os.path.splitext(file_name)[1].lower()
                summary['by_extension'][ext] = summary['by_extension'].get(ext, 0) + 1
    
    return summary

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

def print_directory_summary(directory: str, title: str = None) -> None:
    """Print summary of directory contents"""
    
    if title:
        print(f"\n📂 {title}")
        print("-" * len(title))
    
    summary = get_file_summary(directory)
    
    if summary['total_files'] == 0:
        print("   (empty)")
        return
    
    print(f"   Files: {summary['total_files']}")
    print(f"   Size: {format_file_size(summary['total_size'])}")
    
    if summary['by_extension']:
        print("   Types:")
        for ext, count in sorted(summary['by_extension'].items()):
            ext_display = ext if ext else "(no extension)"
            print(f"     {ext_display}: {count}")

class AnalysisSession:
    """Manage an analysis session with organized output"""
    
    def __init__(self, base_output_dir: str, session_name: str = None):
        self.base_output_dir = base_output_dir
        self.session_name = session_name or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.session_dir = os.path.join(base_output_dir, "sessions", self.session_name)
        
        # Create session structure
        self.dirs = {
            'session': self.session_dir,
            'charts': os.path.join(self.session_dir, 'charts'),
            'reports': os.path.join(self.session_dir, 'reports'),
            'data': os.path.join(self.session_dir, 'data'),
            'logs': os.path.join(self.session_dir, 'logs')
        }
        
        for dir_path in self.dirs.values():
            os.makedirs(dir_path, exist_ok=True)
        
        self.start_time = datetime.now()
        self.session_data = {
            'session_name': self.session_name,
            'start_time': self.start_time.isoformat(),
            'files_created': [],
            'status': 'running'
        }
    
    def add_file(self, file_path: str, file_type: str = 'data') -> str:
        """Add a file to the session"""
        if file_type in self.dirs:
            target_dir = self.dirs[file_type]
            file_name = os.path.basename(file_path)
            target_path = os.path.join(target_dir, file_name)
            
            if file_path != target_path:
                shutil.copy2(file_path, target_path)
            
            self.session_data['files_created'].append({
                'file_path': target_path,
                'file_type': file_type,
                'timestamp': datetime.now().isoformat()
            })
            
            return target_path
        
        return file_path
    
    def finalize(self) -> str:
        """Finalize the session and save metadata"""
        self.session_data['end_time'] = datetime.now().isoformat()
        self.session_data['duration_seconds'] = (datetime.now() - self.start_time).total_seconds()
        self.session_data['status'] = 'completed'
        
        # Save session metadata
        metadata_file = os.path.join(self.session_dir, 'session_metadata.json')
        save_json_data(self.session_data, metadata_file)
        
        return self.session_dir
    
    def get_summary(self) -> Dict[str, Any]:
        """Get session summary"""
        summary = {
            'session_name': self.session_name,
            'session_dir': self.session_dir,
            'files_by_type': {}
        }
        
        for file_type, dir_path in self.dirs.items():
            if file_type != 'session':
                summary['files_by_type'][file_type] = get_file_summary(dir_path)
        
        return summary
