# Capacity Planning: 1000 Users @ <1s (Ollama)

## Verified Baseline
- **Configuration**: 10 Nodes, `OLLAMA_NUM_PARALLEL=8`.
- **Total Capacity**: 80 Parallel Slots (10 nodes * 8).
- **Benchmark (50 Users)**:
    - **Queue Depth**: 0 (50 users < 80 slots).
    - **Throughput**: ~18 RPS.
    - **Latency**: ~2.7s.

## The Bottleneck: Inference Latency
Even with **zero queuing**, the latency is **~2.7s**. 
This is the raw time for Ollama to process a request (Prompt Eval + Token Generation).
To get to **<1s**, we need to speed up the *inference itself*, not just capacity.

### Can we speed up Ollama?
- **Parallelism Impact**: Higher `NUM_PARALLEL` splits the GPU compute. 
    - At `Parallel=1`, latency might be 1.0s.
    - At `Parallel=8`, latency slows to 2.7s (sharing compute).
- **Trade-off**: To get <1s, we likely need to **Lower Parallelism per Node** (dedicating more GPU to each user) and **Increase Node Count**.

## Scaling Math (Target: 1000 Concurrent Users)
Since our goal is **Throughput** (serving 1000 users) with **Low Latency** (<1s), we assume:
- **Max Latency Target**: 1.0s.
- **Estimated Parallelism for 1.0s**: Likely `Parallel=1` or `Parallel=2` (Pending verification).

### scenario A: Parallelism = 2 (Conservative, Fast)
- **Capacity per Node**: 2 Active Users.
- **Required Capacity**: 1000 Users.
- **Node Count**: 1000 / 2 = **500 Nodes**.
- **Cost**: 500 * L4 ($1.5/hr) = $750/hr. (Expensive).

### Scenario B: Parallelism = 8 (Current Config)
- **Capacity per Node**: 8 Active Users.
- **Node Count**: 1000 / 8 = **125 Nodes**.
- **Observed Latency**: ~2.7s. (Misses <1s target).

### Scenario C: Parallelism = 4 (Balanced)
- **Est. Latency**: ~1.5s? (Guess).
- **Node Count**: 250 Nodes.

## Conclusion
To hit strictly **<1s** with Ollama (which lacks continuous batching), you effectively need **1 GPU per 1-2 Users**.
**Constraint**: Ollama's architecture forces a trade-off: Capacity (Parallelism) kills Latency.
**Recommendation**: 
1.  **For <1s Latency**: Requires **500+ Nodes** (Parallel=2).
2.  **For <3s Latency**: Requires **125 Nodes** (Parallel=8).

> **Note**: vLLM (Continuous Batching) typically handles 50+ streams at <1s latency on L4. This highlights why the migration (and Authentication) is valuable for cost. But sticking to Ollama implies massive hardware scaling.

## Final Answer for User
**To achieve 1000 users at <1s latency with Ollama:**
You likely need **~500 Nodes** (setting `OLLAMA_NUM_PARALLEL=2` to prioritize speed).
With the current `Parallel=8` (2.7s), you would need **125 Nodes** but latency would stay ~2.7s.
