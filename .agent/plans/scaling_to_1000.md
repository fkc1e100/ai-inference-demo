# Scaling Analysis: Path to 1000 Users @ <1s Latency

## Current Baseline (50 Users)
- **Architecture**: 10 x NVIDIA L4 Nodes (Ollama, Serial Execution).
- **Throughput**: ~5 Requests Per Second (RPS) total across cluster.
- **Latency**: ~9.7s average.
- **Bottleneck**: Request Queuing (Queue scheduling delay >> Inference time).

## The Challenge: 200x Throughput Gap
To serve **1000 Concurrent Users** with **<1s Latency**:
- **Requirement**: Processing ~1000 active requests in parallel.
- **Current Parallelism**: 10 active requests (1 per node).
- **Gap**: The system needs effectively **1000 Parallel Slots**.

## Solution Roadmap
We can achieve this via a combination of software optimization (Parallelism) and hardware scaling (More Nodes).

### Phase 1: Software Optimization (Free Performance)
Currently, `OLLAMA_NUM_PARALLEL` defaults to 1, meaning 23GB of the L4's 24GB VRAM sits idle while 1 request runs.
- **Action**: Increase `OLLAMA_NUM_PARALLEL` to **8** or **16**.
- **Math**: 
    - Gemma 4B Model: ~3GB VRAM.
    - KV Cache per slot (2k context): ~1GB.
    - Node Capacity (24GB VRAM): Can fit model + ~16 active slots.
    - **Result**: 10 nodes x 16 slots = **160 Parallel Slots**.
- **Impact**: Latency for 50 users drops to <1s immediately. Throughput increases 10-15x (approx 50-75 RPS).

### Phase 2: Engine Upgrade (Production Grade)
Ollama is excellent for ease-of-use but lacks **Continuous Batching** (efficiently merging tokens from different users into single GPU ops). 
- **Action**: Switch inference backend to **vLLM** or **TGI**.
- **Benefit**: vLLM on L4 can handle much higher effective batch sizes than Ollama's fixed slots.
- **Estimated Capacity**: ~50 concurrent streams per L4 node with good latency.
- **Result**: 10 nodes x 50 streams = **500 Parallel Slots**.

### Phase 3: Hardware Scaling (Closing the Gap)
Even with vLLM (500 capacity), satisfying 1000 pure concurrent users requires more metal.
- **Action**: Scale from 10 nodes to **20 or 25 Nodes**.
- **Math**: 20 Nodes x 50 Streams/Node = **1000 Concurrent Streams**.
- **Cost**: 20 x L4 GPUs is reasonable (~$15/hr).

## Recommended Implementation Plan
1.  **Immediate**: Tune `OLLAMA_NUM_PARALLEL` to `8` in `values.yaml` and re-test 50 users. verifying <1s.
2.  **Next**: Ramp test to 160 users (Cluster Limit with Optimization).
3.  **Final**: To reach 1000, plan migration to vLLM and double node count.

## Summary Table
| Configuration | Nodes | Parallelism/Node | Total Capacity | Est. Latency (1000 Users) |
| :--- | :--- | :--- | :--- | :--- |
| **Current** | 10 | 1 | 10 | ~100s (Timeout) |
| **Tuned Ollama** | 10 | 16 | 160 | ~6-8s |
| **vLLM** | 10 | ~50 | 500 | ~2s |
| **vLLM + Scale** | **25** | **~50** | **1250** | **< 1s** |
