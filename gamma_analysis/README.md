# Gamma Control Analysis Suite

This folder contains a comprehensive analysis system for studying the effect of gamma penalty values on path planning violations and operational efficiency.

## 🚀 **QUICK START - One File Solution**

**For immediate gamma analysis, just run the master script:**

```bash
# Quick demo analysis
python3 master_gamma_analysis.py --demo

# Custom gamma values  
python3 master_gamma_analysis.py --demo --gamma-values 1,10,50,100,200

# Named experiment
python3 master_gamma_analysis.py --demo --experiment-name "my_analysis"
```

**The master script (`master_gamma_analysis.py`) consolidates ALL functionality into one comprehensive file. It generates professional charts, detailed reports, and organized data - everything you need!**

📖 **See `MASTER_QUICK_START.md` for complete usage guide.**

---

## Overview

The gamma penalty mechanism acts as a "control knob" that allows system designers to fine-tune the balance between strict rule adherence and operational efficiency. This analysis suite demonstrates how varying gamma from low to high values affects:

- **Violation rates**: Number of constraint violations
- **Path costs**: Computational and operational costs  
- **Planning efficiency**: Overall system performance
- **Compliance levels**: Adherence to restrictions

## Key Insight

> **"With a low gamma, the system decided it was 'cheaper' to violate the constraint and pay the small penalty. As we increased gamma to a medium value, the number of violations decreased. And with a high gamma, the penalty became too costly to ignore, resulting in zero violations."**

This demonstrates that gamma acts as an effective control parameter for balancing rule compliance with operational efficiency.

## Key Concept: Escape Edges

**Escape edges** are artificial edges with gamma penalty cost that allow AGVs to violate restrictions when necessary. When an AGV uses an escape edge (carries flow), it indicates a violation with penalty cost = flow × gamma.

## Files Structure


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
```

## Quick Start

### 1. Run Main Analysis (Recommended)
```bash
cd gamma_analysis
python gamma_analysis.py
```

This runs the complete analysis pipeline with:
- Organized output structure
- Configurable parameters
- Automatic file organization
- Session management

### 2. Run Demonstration
```bash
python gamma_analysis.py --demo
```

Quick demonstration with simulated data showing gamma control effects.

### 3. Custom Configuration
```bash
python gamma_analysis.py --config simple_config.json --gamma-values 0.1,1.0,10.0
```

Use specific configuration and gamma values.

### 4. Alternative Scripts
```bash
# Configurable analysis with flow explanation
python configurable_gamma_analysis.py

# Simple test
python simple_gamma_test.py --test-gamma
```

## Expected Results

The experiment demonstrates the **gamma control effect**:

### Low Gamma (1-10)
- **Behavior**: System accepts violations (cheaper than compliance)
- **Result**: Higher number of violations
- **Use case**: Maximum operational flexibility

### Medium Gamma (50-200) 
- **Behavior**: Balanced approach between compliance and efficiency
- **Result**: Moderate violations
- **Use case**: Standard operational balance

### High Gamma (400-800)
- **Behavior**: Strict rule adherence (violations too costly)
- **Result**: Zero or minimal violations
- **Use case**: Safety-critical or regulated environments

## Generated Outputs

### 1. Analysis Reports (`output/*.md`)
- Detailed markdown reports with insights
- Summary tables of results
- Key findings and recommendations

### 2. Visualization Charts (`output/*.png`)
- **Main Chart**: Violations vs Gamma (demonstrates control knob effect)
- **Detailed Charts**: Multi-metric analysis including penalty costs, simulation time, control effectiveness

### 3. Raw Data (`output/*.json`)
- Complete experimental results
- Detailed violation information
- Escape edge analysis data

## Key Insights Demonstrated

1. **Control Knob Effect**: Gamma effectively controls violation behavior
2. **Trade-off Balance**: Clear trade-off between compliance and efficiency
3. **Design Flexibility**: System designers can tune gamma for specific needs
4. **Violation Detection**: Flow through escape edges accurately indicates violations

## Integration with Main System

The analysis suite integrates with the main simulation system through:
- `RestrictionForTimeFrameController` enhanced with gamma control methods
- Automated simulation execution with different gamma values
- Real-time violation detection through escape edge flow analysis

## Technical Details

### Escape Edge Detection
```python
# Only artificial edges with gamma cost > 0 are escape edges
if source > 80 and dest > 80 and cost > 0:
    # This is an escape edge that can indicate violations
```

### Violation Detection
```python
# Check flow through escape edges  
if flow_value > 0:
    # Violation detected: penalty = flow × gamma
    violation_cost = flow_value * gamma_cost
```

## Understanding Flow Values and Violations

### Why More Violations Than AGVs?

**Q: I have 2 AGVs but see 8 violations. Why?**

**A: Flow violations ≠ AGV count**

Flow values represent **AGV-time usage units**, not just the number of AGVs. Here's why you see more violations:

#### Common Scenarios:

1. **Time-Based Violations**
   ```
   AGV 1 path: A → B → C (3 time steps)
   AGV 2 path: D → B → E (2 time steps)
   
   If both use restricted edge B→C:
   • Time step 1: AGV 2 violation (+1)
   • Time step 2: AGV 1 violation (+1) 
   • Time step 3: AGV 1 violation (+1)
   Total: 3 violations from 2 AGVs
   ```

2. **Capacity Overflow**
   ```
   Edge capacity: 1 AGV per time step
   Demand: 3 AGV-time units
   Overflow: 2 units → 2 violations
   ```

3. **Multiple Restrictions**
   ```
   Single AGV can violate:
   • Capacity limit: +2 flow
   • Time window: +3 flow
   • Priority lane: +3 flow
   Total: 8 violations from 1 AGV
   ```

#### Flow Formula:
```
Violations = Flow through escape edges
Flow = AGV usage × Time steps × Restriction violations
Penalty = Flow × Gamma
```

## Configuration System

You can customize all analysis parameters using configuration files:

#### Quick Setup:
```bash
# Use default configuration
python3 configurable_gamma_analysis.py

# Use custom configuration  
python3 configurable_gamma_analysis.py --config simple_config.json
```

#### Key Configuration Options:

```json
{
  "gamma_settings": {
    "gamma_values": [0.0, 1.0, 5.0, 10.0],  // Test these gamma values
    "default_gamma": 1.0
  },
  "agv_configuration": {
    "num_agvs": 2,                           // Number of AGVs in simulation
    "agv_speed": 1.0
  },
  "simulation_parameters": {
    "num_runs_per_gamma": 3,                 // Runs per gamma for statistics
    "timeout_seconds": 60,                   // Max simulation time
    "map_file": "simplest.txt"               // Map to use
  },
  "violation_analysis": {
    "min_violation_threshold": 0.1,          // Minimum flow to count as violation
    "detailed_reporting": true
  }
}
```

#### Configuration Files Available:
- **`config.json`** - Full configuration with all options
- **`simple_config.json`** - Basic configuration for quick tests
- Create your own for custom scenarios

## Requirements

- Python 3.x
- matplotlib (for visualization)
- pandas (for data analysis)
- numpy (for numerical operations)
- Access to main simulation system (main.py, controllers, models)

## Usage Notes

1. **Run from gamma_analysis folder**: Scripts expect to find main.py in parent directory
2. **Simulation timeout**: Each simulation has 60-second timeout
3. **Backup handling**: Original TSG files are automatically backed up and restored
4. **Error handling**: Robust error handling for simulation failures

## Customization

### Modify Gamma Values
Edit `gamma_values` list in `run_gamma_analysis.py`:
```python
gamma_values = [1, 10, 50, 100, 200, 400, 800]  # Customize as needed
```

### Change Simulation Parameters
Modify `simulation_input` in `run_gamma_analysis.py` to test different scenarios:
- Map file (currently `simplest.txt`)
- Time horizon
- AGV count
- Restriction parameters

### Custom Analysis
Use `GammaAnalysisRunner` class directly for custom experiments:
```python
from gamma_control_analyzer import GammaAnalysisRunner

analyzer = GammaAnalysisRunner(output_dir="my_experiment")
results = analyzer.run_gamma_experiment(my_gamma_values, my_simulation_func, "my_experiment")
```

This analysis suite provides comprehensive tools for understanding and demonstrating the gamma control mechanism's effectiveness as a system design parameter.
