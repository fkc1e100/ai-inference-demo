# Implementation Plan - Stabilize Scaling & Verify Performance

## Status Analysis
- **Current State**: 4/10 Replicas Ready.
- **Failures Identified**:
  1. **HPA Conflict**: HPA downscaling logic (`minReplicas` defaults/low) caused the cluster to shrink from 10 to 4 nodes, fighting the manual scale-out.
  2. **Memory OOM**: `ollama` processes are consuming ~51GB RAM on 48GB nodes, causing `OOMKilled` events and pod crashes.

## Objective
- Stabilize the cluster at 10 replicas (utilizing full reserved capacity).
- Verify <1s response latency for 50 concurrent users.

## Proposed Changes
1. **Pin Scalability (`helm/ai-inference/values.yaml`)**:
   - Set `autoscaling.minReplicas: 10` (matching `maxReplicas`) to disable downscaling during the test duration.

2. **Optimize Memory (`helm/ai-inference/values.yaml`)**:
   - **Limit**: Set `resources.limits.memory: 40Gi`.
   - **Request**: Set `resources.requests.memory: 40Gi`.
   - This reserves 8GB for System/Kubelet, preventing node-level OOM kills and forcing the application to manage its cache or fail gracefully (instead of crashing the node).

3. **Execution Sequence**:
   - **Apply**: `helm upgrade ai-inference ./helm/ai-inference`.
   - **Wait**: `kubectl wait --for=condition=available --timeout=300s deployment/ai-inference`.
   - **Connect**: Verify `curl http://localhost:8000/api/tags` via port-forward.
   - **Test**: Run `python3 load_test.py --users 50 --duration 60`.
   - **Report**: Analyze latency and throughput.

## Documentation
- Update `SCALING.md` to reflect the "Pinned Scale" strategy for load testing and the memory requirements for `gemma3-4b` on L4 nodes.
