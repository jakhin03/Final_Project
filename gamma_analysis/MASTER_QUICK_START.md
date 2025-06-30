# Master Gamma Analysis - Quick Start Guide

## Single File Solution ✨

The `master_gamma_analysis.py` file consolidates ALL gamma analysis functionality into one comprehensive script. You only need to run this one file for complete gamma control analysis!

## Quick Usage

### Basic Demo Run
```bash
python3 master_gamma_analysis.py --demo
```

### Custom Gamma Values
```bash
python3 master_gamma_analysis.py --demo --gamma-values 1,5,10,50,100,200,400
```

### Named Experiment
```bash
python3 master_gamma_analysis.py --demo --experiment-name "my_test" --gamma-values 1,10,100
```

### Real Simulation (if available)
```bash
python3 master_gamma_analysis.py --real --gamma-values 1,10,50,100
```

## What You Get

Running the master script generates:

### 📊 **Charts** (PNG + PDF)
- **Gamma Control Analysis**: 4-panel comprehensive visualization
  - Violations vs Gamma
  - Penalty Cost vs Gamma  
  - Violation Flow vs Gamma
  - Effectiveness comparison
- **Escape Edge Analysis**: Escape edge utilization charts

### 📋 **Reports** (Markdown)
- **Comprehensive Analysis Report**: Executive summary, insights, technical details
- **Flow explanation**: Why flow can exceed AGV count
- **Key insights**: Gamma control effectiveness

### 💾 **Data** (JSON + CSV)
- **Raw experiment data**: All results in structured format
- **Configuration**: Experiment settings and parameters

### 📁 **Organized Structure**
```
output/experiments/gamma_experiment_YYYYMMDD_HHMMSS/
├── charts/          # All visualizations
├── reports/         # Analysis reports  
├── data/           # Raw and processed data
└── tsg_backups/    # TSG file backups (real simulation)
```

## Key Features

✅ **Complete Analysis**: All gamma functionality in one script  
✅ **Professional Visualizations**: Publication-ready charts  
✅ **Comprehensive Reports**: Detailed analysis and insights  
✅ **Organized Output**: Structured results by experiment  
✅ **Demo Mode**: Works without real simulation  
✅ **Real Integration**: Connects to actual simulation system  
✅ **Escape Edge Detection**: Identifies gamma penalty edges  
✅ **Flow Analysis**: Measures actual violations  
✅ **Configurable**: Custom gamma values and settings  

## Command Line Options

```
--demo                  Run demonstration with simulated data
--real                  Run with real simulation integration  
--gamma-values X,Y,Z    Test specific gamma values (e.g., 1,10,50,100)
--config FILE          Use custom configuration file
--output-dir DIR       Specify output directory  
--experiment-name NAME  Name for this experiment
--help                 Show detailed help
```

## Examples

### Quick Test
```bash
# Fast demo with default gamma values
python3 master_gamma_analysis.py --demo
```

### Custom Analysis  
```bash
# Custom gamma range with named experiment
python3 master_gamma_analysis.py --demo \
  --gamma-values 1,2,5,10,20,50,100,200 \
  --experiment-name "detailed_study" \
  --output-dir "my_results"
```

### Research Study
```bash
# Comprehensive analysis for research
python3 master_gamma_analysis.py --demo \
  --gamma-values 0.1,0.5,1,2,5,10,25,50,100,200,500,1000 \
  --experiment-name "research_gamma_study_2025"
```

## Key Insights From Results

The master script demonstrates:

1. **🔻 Low Gamma (1-10)**: More violations, cheaper penalties
2. **⚖️ Medium Gamma (10-50)**: Balanced efficiency vs compliance  
3. **🔺 High Gamma (100+)**: Strict compliance, minimal violations
4. **🎯 Optimal Range**: Typically 50-200 for balanced operation

## Flow Value Understanding

**Why flow can exceed AGV count:**
- Multiple AGVs violating same restriction
- Single AGV violating multiple times  
- Cumulative violation intensity across time
- Network flow representation of constraint violations

---

**One script. Complete analysis. Professional results.**
