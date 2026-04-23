# Lab 16 Benchmark Report

## Metadata
- Dataset: hotpot_100.json
- Mode: real
- Records: 200
- Agents: react, reflexion

## Summary
| Metric | ReAct | Reflexion | Delta |
|---|---:|---:|---:|
| EM | 0.62 | 0.89 | 0.27 |
| Avg attempts | 1 | 1.59 | 0.59 |
| Avg token estimate | 1958.65 | 4250.14 | 2291.49 |
| Avg latency (ms) | 46926.76 | 119051.93 | 72125.17 |

## Failure modes
```json
{
  "none": 151,
  "incomplete_multi_hop": 11,
  "wrong_final_answer": 13,
  "entity_drift": 14,
  "looping": 11
}
```

## Extensions implemented
- structured_evaluator
- reflection_memory
- benchmark_report_json
- mock_mode_for_autograding
- adaptive_max_attempts
- memory_compression
- plan_then_execute

## Discussion
Reflexion is extremely beneficial when the first attempt stops after the first hop or drifts to a completely wrong second-hop entity. However, the tradeoff is significantly higher attempts, token cost, and execution latency. By utilizing advanced techniques like memory compression and adaptive max attempts, we effectively manage prompt lengths and prevent the agent from infinitely looping without making meaningful progress, which solves many fundamental problems in ReAct.
