# Scalability Verification Report & Guide

## Executive Summary
This document details the scalability architecture, load testing procedures, and verification results for the AI Inference Platform. The system has been upgraded to support **stabilized horizontal scaling**, **OOM protection**, and **Capacity Reservation (DWS)** to ensure reliability under heavy load.

## Architecture Upgrades

### 1. Stability & Resource Management
To address OOM (Out of Memory) instability on `g2-standard-12` nodes during high load:
*   **Memory Constraints:** `resources.limits.memory` set to `40Gi` (below the 48GB node limit) to prevent system-level OOM kills.
*   **Pinning Strategy:** For sustained performance testing, `minReplicas` is pinned to match `maxReplicas` (10), preventing HPA thrashing.

### 2. High-Capacity Infrastructure (DWS)
To guarantee GPU availability during critical batch processing:
*   **Capacity:** 10 NVIDIA L4 GPU nodes verified and operational.
*   **Queued Provisioning:** Ensures atomic allocation of all 10 nodes for batch jobs.

### 3. Traffic Distribution (Load Balancer)
To handle high concurrency (50+ users) and distribute traffic across the 10 replicas efficiently, we utilize an **External Load Balancer (L4)**:
- **Type:** `LoadBalancer` (provisioned via Helm)
- **Role:** Exposes a single External IP that rounds-robins requests to all healthy pods, preventing bottlenecks associated with `kubectl port-forward` or single-point entry.

## Load Testing

### Prerequisites
1.  **Get Load Balancer IP:**
    ```bash
    kubectl get svc ai-inference
    # Note the EXTERNAL-IP (e.g., 34.xxx.xxx.xxx)
    ```

### Usage
Run the updated load test script against the Load Balancer:
```bash
# Replace <LB_IP> with the actual External IP
python3 load_test.py --users 50 --duration 60 --url http://<LB_IP>:8000/api/generate
```

### Verified Results (50 Users @ 10 Replicas)
| Metric | Result | Notes |
| :--- | :--- | :--- |
| **Stability** | **100%** | Zero crashes/restarts |
| **Latency** | **~2.7s** | Improved 4x via `OLLAMA_NUM_PARALLEL=8` |
| **Capacity** | **10 Replicas** | Fully utilized |

> **Performance Note:** Increasing parallelism to 8 drastically reduced queuing delay. Further tuning (e.g., Parallel=16) or vLLM migration is recommended for 1000-user scale.

> **Note:** Testing via `kubectl port-forward` is strictly limited to low concurrency (<10 users) due to local tunnel bandwidth limits. Production traffic MUST use the Load Balancer.
