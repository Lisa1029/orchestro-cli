# Parallel Execution Performance Benchmark

Generated: 2025-11-16 12:10:44

## Worker Count Benchmark

Tests parallel speedup with different worker counts.

| Workers | Time (s) | Speedup | Throughput (scenarios/s) |
|---------|----------|---------|--------------------------|
| 1 | 47.53 | 0.96x | 0.42 |
| 2 | 26.27 | 1.78x | 0.76 |
| 4 | 14.74 | 3.27x | 1.36 |
| 8 | 10.22 | 5.25x | 1.96 |

## Scenario Complexity Benchmark

Tests execution time for different scenario complexities.

| Complexity | Total Time (s) | Avg Duration (s) | Median (s) |
|------------|----------------|------------------|------------|
| simple | 6.47 | 2.12 | 2.12 |
| medium | 8.49 | 2.41 | 2.34 |
| complex | 9.88 | 2.68 | 2.61 |

## Scalability Benchmark

Tests performance with increasing scenario count.

| Scenarios | Time (s) | Throughput | Time/Scenario (s) |
|-----------|----------|------------|-------------------|
| 5 | 5.24 | 0.95/s | 1.05 |
| 10 | 6.48 | 1.54/s | 0.65 |
| 20 | 11.55 | 1.73/s | 0.58 |
| 40 | 24.98 | 1.60/s | 0.62 |

## Priority Scheduling Benchmark

- **Total Time**: 10.72s
- **High Priority First**: True
- **Time Difference**: 5.12s

---

*Benchmark complete*
