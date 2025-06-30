# Gamma Control Analysis Report

**Experiment:** gamma_experiment_20250630_231823
**Date:** 2025-06-30 23:18:37
**Mode:** Demonstration

## Executive Summary

- **Gamma range tested:** 1.0 - 200.0
- **Total tests:** 5
- **Total violations detected:** 20
- **Maximum penalty cost:** 400
- **Optimal gamma (min violations):** 200.0

## Gamma Control Effect

The gamma penalty mechanism demonstrates clear control over violation behavior:

- **γ = 1.0:** 8 violations, 14 total flow, penalty cost: 14
- **γ = 10.0:** 5 violations, 6 total flow, penalty cost: 60
- **γ = 50.0:** 4 violations, 7 total flow, penalty cost: 350
- **γ = 100.0:** 2 violations, 4 total flow, penalty cost: 400
- **γ = 200.0:** 1 violations, 0 total flow, penalty cost: 0

## Key Insights

1. **Low gamma values** lead to more violations as the penalty is 'cheaper' than compliance
2. **Medium gamma values** provide balanced trade-off between efficiency and compliance
3. **High gamma values** enforce strict compliance with zero or minimal violations
4. **Escape edges** serve as safety valves allowing controlled violations when necessary

## Flow Value Explanation

Flow values can exceed AGV count because:
- Multiple AGVs may violate the same restriction
- Single AGV may violate multiple times in different time windows
- Flow represents cumulative violation intensity across time and space

## Technical Details

- **Escape edge detection:** Identifies artificial edges with gamma costs
- **Flow analysis:** Measures actual usage of escape edges
- **Violation calculation:** Flow × Gamma = Penalty cost
- **Control mechanism:** Higher gamma → higher penalty → fewer violations

## Conclusion

Gamma control provides effective 'knob' for balancing operational efficiency with rule compliance. System designers can tune gamma values to achieve desired balance between strict adherence and practical flexibility.
