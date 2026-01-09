# Walkthrough - Stabilization & Load Balancer Deployment

## Summary
To address system instability and high-concurrency bottlenecks, we implemented three critical fixes:
1.  **OOM Protection**: Constrained pod memory to `40Gi` to prevent crashes on `g2-standard-12` nodes.
2.  **Capacity Pinning**: Locked `minReplicas` to 10 to guarantee full-scale testing capacity.
3.  **Traffic Distribution**: Deployed an External Load Balancer to bypass `port-forward` limitations.

## Key Changes

### 1. Helm Configuration (`values.yaml`)
```yaml
resources:
  limits:
    memory: "40Gi" # Fits within 48GB node
service:
  type: LoadBalancer # Replaces ClusterIP
autoscaling:
  minReplicas: 10 # Prevents downscaling
```

## Verification Results

### Load Test (50 Users, 60s)
- **Target**: `http://34.139.212.96:8000` (External LB)
- **Requests**: 300
- **Errors**: 0 (100% Success)
- **Avg Latency**: 9.75s

### Analysis
The system is now **fully stable** under load. 
The ~10s latency is consistent with a queue depth of 5 (50 users / 10 nodes) and default serial processing. 
**Next Step for Performance:** Tune `OLLAMA_NUM_PARALLEL` to process multiple requests per GPU execution cycle.

## Artifacts
- [SCALING.md](file:///usr/local/google/home/fcurrie/gke-inference-demo/docs/SCALING.md): Updated with LB instructions and results.
- `values.yaml`: Updated configuration.
