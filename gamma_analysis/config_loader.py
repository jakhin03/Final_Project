#!/usr/bin/env python3
"""
Configuration Loader for Gamma Analysis

This module loads and validates configuration settings for the gamma analysis suite.
"""

import json
import os
from typing import Dict, Any, List, Optional

class GammaAnalysisConfig:
    """Configuration manager for gamma analysis experiments"""
    
    def __init__(self, config_file: str = "config.json"):
        """
        Initialize configuration manager
        
        Args:
            config_file: Path to the configuration JSON file
        """
        self.config_file = config_file
        self.config = self._load_config()
        self._validate_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        
        if not os.path.exists(self.config_file):
            print(f"⚠️  Config file {self.config_file} not found, using defaults")
            return self._get_default_config()
        
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            print(f"✅ Configuration loaded from {self.config_file}")
            return config
        except Exception as e:
            print(f"❌ Error loading config: {e}")
            print("Using default configuration")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "gamma_settings": {
                "gamma_values": [0.0, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
                "default_gamma": 1.0
            },
            "simulation_parameters": {
                "num_runs_per_gamma": 3,
                "timeout_seconds": 60,
                "map_file": "simplest.txt"
            },
            "agv_configuration": {
                "num_agvs": 2
            },
            "output_settings": {
                "output_directory": "output",
                "save_charts": True,
                "save_reports": True
            }
        }
    
    def _validate_config(self):
        """Validate configuration values"""
        
        # Validate gamma values
        gamma_values = self.get_gamma_values()
        if not gamma_values or not isinstance(gamma_values, list):
            raise ValueError("gamma_values must be a non-empty list")
        
        if any(g < 0 for g in gamma_values):
            raise ValueError("All gamma values must be non-negative")
        
        # Validate simulation parameters
        if self.get_num_runs_per_gamma() < 1:
            raise ValueError("num_runs_per_gamma must be at least 1")
        
        if self.get_num_agvs() < 1:
            raise ValueError("num_agvs must be at least 1")
        
        print("✅ Configuration validation passed")
    
    # Getter methods for easy access to configuration values
    
    def get_gamma_values(self) -> List[float]:
        """Get list of gamma values to test"""
        return self.config.get("gamma_settings", {}).get("gamma_values", [1.0, 10.0])
    
    def get_default_gamma(self) -> float:
        """Get default gamma value"""
        return self.config.get("gamma_settings", {}).get("default_gamma", 1.0)
    
    def get_num_runs_per_gamma(self) -> int:
        """Get number of simulation runs per gamma value"""
        return self.config.get("simulation_parameters", {}).get("num_runs_per_gamma", 3)
    
    def get_timeout_seconds(self) -> int:
        """Get simulation timeout in seconds"""
        return self.config.get("simulation_parameters", {}).get("timeout_seconds", 60)
    
    def get_map_file(self) -> str:
        """Get map file name"""
        return self.config.get("simulation_parameters", {}).get("map_file", "simplest.txt")
    
    def get_num_agvs(self) -> int:
        """Get number of AGVs"""
        return self.config.get("agv_configuration", {}).get("num_agvs", 2)
    
    def get_output_directory(self) -> str:
        """Get output directory"""
        return self.config.get("output_settings", {}).get("output_directory", "output")
    
    def should_save_charts(self) -> bool:
        """Check if charts should be saved"""
        return self.config.get("output_settings", {}).get("save_charts", True)
    
    def should_save_reports(self) -> bool:
        """Check if reports should be saved"""
        return self.config.get("output_settings", {}).get("save_reports", True)
    
    def get_chart_formats(self) -> List[str]:
        """Get chart output formats"""
        return self.config.get("output_settings", {}).get("chart_formats", ["png"])
    
    def get_violation_threshold(self) -> float:
        """Get minimum violation threshold"""
        return self.config.get("violation_analysis", {}).get("min_violation_threshold", 0.1)
    
    def is_debug_mode(self) -> bool:
        """Check if debug mode is enabled"""
        return self.config.get("advanced_settings", {}).get("debug_mode", False)
    
    def get_scenario(self, scenario_name: str) -> Optional[Dict[str, Any]]:
        """Get custom scenario configuration"""
        scenarios = self.config.get("custom_scenarios", {})
        return scenarios.get(scenario_name)
    
    def list_scenarios(self) -> List[str]:
        """List available custom scenarios"""
        return list(self.config.get("custom_scenarios", {}).keys())
    
    def get_color_scheme(self) -> Dict[str, str]:
        """Get visualization color scheme"""
        return self.config.get("visualization_config", {}).get("color_scheme", {
            "violations": "crimson",
            "costs": "steelblue",
            "efficiency": "purple",
            "success": "green"
        })
    
    def get_figure_size(self) -> List[int]:
        """Get figure size for charts"""
        return self.config.get("visualization_config", {}).get("figure_size", [12, 8])
    
    def get_dpi(self) -> int:
        """Get DPI for chart output"""
        return self.config.get("visualization_config", {}).get("dpi", 300)
    
    def print_config_summary(self):
        """Print a summary of the current configuration"""
        
        print("\n" + "="*50)
        print("GAMMA ANALYSIS CONFIGURATION SUMMARY")
        print("="*50)
        
        print(f"📁 Config file: {self.config_file}")
        print(f"🎛️  Gamma values: {self.get_gamma_values()}")
        print(f"🔄 Runs per gamma: {self.get_num_runs_per_gamma()}")
        print(f"🚗 Number of AGVs: {self.get_num_agvs()}")
        print(f"🗺️  Map file: {self.get_map_file()}")
        print(f"⏱️  Timeout: {self.get_timeout_seconds()}s")
        print(f"📂 Output directory: {self.get_output_directory()}")
        print(f"📊 Save charts: {self.should_save_charts()}")
        print(f"📄 Save reports: {self.should_save_reports()}")
        print(f"🎨 Chart formats: {self.get_chart_formats()}")
        
        scenarios = self.list_scenarios()
        if scenarios:
            print(f"📋 Available scenarios: {scenarios}")
        
        print(f"🐛 Debug mode: {self.is_debug_mode()}")
        print("="*50)
    
    def update_config(self, updates: Dict[str, Any]):
        """Update configuration values"""
        
        def deep_update(base_dict, update_dict):
            for key, value in update_dict.items():
                if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                    deep_update(base_dict[key], value)
                else:
                    base_dict[key] = value
        
        deep_update(self.config, updates)
        self._validate_config()
        print("✅ Configuration updated")
    
    def save_config(self, output_file: Optional[str] = None):
        """Save current configuration to file"""
        
        output_file = output_file or self.config_file
        
        try:
            with open(output_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            print(f"✅ Configuration saved to {output_file}")
        except Exception as e:
            print(f"❌ Error saving configuration: {e}")

def load_config(config_file: str = "config.json") -> GammaAnalysisConfig:
    """
    Convenience function to load configuration
    
    Args:
        config_file: Path to configuration file
        
    Returns:
        GammaAnalysisConfig instance
    """
    return GammaAnalysisConfig(config_file)

if __name__ == "__main__":
    # Test configuration loading
    config = load_config()
    config.print_config_summary()
    
    # Example of updating configuration
    print("\n🔧 Testing configuration updates...")
    config.update_config({
        "agv_configuration": {
            "num_agvs": 3
        },
        "gamma_settings": {
            "gamma_values": [0.0, 1.0, 5.0, 20.0]
        }
    })
    
    print("\n📊 Updated configuration:")
    config.print_config_summary()
