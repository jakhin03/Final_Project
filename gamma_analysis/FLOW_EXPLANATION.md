# Understanding Flow Values and Violations

## What is Flow Value?

**Flow value** in the context of network flow represents the amount of "flow" passing through an edge. In our path planning system:

- **Flow ≠ Number of AGVs**
- **Flow = AGV-time units** or **path usage intensity**

## Why More Violations Than AGVs?

With **2 AGVs** but **8 violations**, here's what's happening:

### Scenario 1: Time-Based Violations
```
AGV 1 path: A → B → C (takes 3 time steps)
AGV 2 path: D → B → E (takes 2 time steps)

If both AGVs pass through restricted edge B→C:
- AGV 1 uses B→C at time t=2 (1 violation)
- AGV 1 uses B→C at time t=3 (1 violation) 
- AGV 2 uses B→C at time t=1 (1 violation)
- etc.

Total: Multiple violations from same AGVs at different times
```

### Scenario 2: Multi-Path Violations
```
Single AGV might violate multiple restrictions:
- Violates restriction 1 (capacity limit): +2 flow
- Violates restriction 2 (time window): +3 flow  
- Violates restriction 3 (priority lane): +3 flow

Total: 8 violations from complex path requirements
```

### Scenario 3: Flow Accumulation
```
In network flow, "flow" can accumulate:
- Base flow requirement: 5 units
- Available capacity: 2 units
- Excess flow through escape edge: 3 units
- Multiple time periods: 3 × 2 = 6 violations
- Plus additional constraints: +2 violations
Total: 8 violations
```

## Flow Value Examples

### Example 1: Simple Case
```
Edge capacity: 1 AGV per time step
Actual demand: 3 AGV-time units
Flow through escape edge: 2 units
→ 2 violations
```

### Example 2: Complex Case  
```
Restriction: "Max 1 AGV in corridor per 5-minute window"
Actual usage: 4 AGV passages in same window
Flow through escape edge: 3 units
→ 3 violations (excess demand)
```

### Example 3: Time-Extended Case
```
AGV path spans 4 time steps
Each step violates capacity by 1 unit
Total flow through escape edges: 4 units
→ 4 violations from single AGV
```

## Key Points

1. **Flow ≠ AGV Count**: Flow represents usage intensity, not just count
2. **Time Dimension**: Same AGV can cause multiple violations over time
3. **Multiple Restrictions**: Single AGV can violate different restrictions
4. **Capacity Overflow**: Violations = excess demand beyond capacity
5. **Network Flow Math**: Flow optimization can distribute violations

## Validation

To verify the violations make sense:

```python
# Check violation details
violations = analyzer.analyze_escape_edge_violations()
for v in violations:
    print(f"Edge {v['source']}→{v['dest']}: {v['flow']} flow units")
    print(f"  Gamma cost: {v['gamma_cost']}")
    print(f"  Penalty: {v['penalty_cost']}")
```

This will show you exactly which edges are being violated and by how much flow.
