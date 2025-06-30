# Gamma Control Analysis Report

**Generated:** 2025-06-30 21:14:32

## Results Summary

| Gamma | Violations | Violation Flow | Penalty Cost |
|-------|------------|---------------|-------------|
| 1 | 8 | 12 | 12 |
| 10 | 5 | 7 | 70 |
| 50 | 3 | 4 | 200 |
| 100 | 2 | 2 | 200 |
| 200 | 1 | 1 | 200 |
| 400 | 0 | 0 | 0 |
| 800 | 0 | 0 | 0 |

## Key Insights

### Gamma Control Effect Demonstrated

- **Lowest Gamma (1)**: 8 violations
- **Highest Gamma (800)**: 0 violations
- **Violation Reduction**: 8 violations eliminated

### Control Knob Analysis

The results clearly demonstrate that gamma acts as an effective 'control knob':

- **Low Gamma (1-10)**: System accepts violations as they are cheaper than strict compliance
- **Medium Gamma (50-200)**: Balanced approach with moderate violation reduction
- **High Gamma (400-800)**: Strict rule adherence as violations become too costly

## Conclusion

This analysis demonstrates that the penalty cost gamma serves as an effective system design parameter, allowing designers to fine-tune the balance between strict rule adherence and operational efficiency based on specific operational requirements.
