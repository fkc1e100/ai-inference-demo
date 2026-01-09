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

### Verified Results (Parallelism Tuning)
| Parallelism | Latency (Avg) | Throughput (10 Nodes) | Use Case |
| :--- | :--- | :--- | :--- |
| **8 (Max)** | ~2.7s | 80 Concurrent | Batch / Throughput Optimized |
| **4 (Balanced)** | ~1.5s - 2.0s | 40 Concurrent | Interactive (<2s target) |

## Capacity Planning (1000 Users)
To scale to **1000 concurrent users** while maintaining **<2s latency**:
1.  **Metric**: Each node handles ~4 users (Parallelism=4).
2.  **Calculation**: 1000 Users / 4 Users per Node = **250 Nodes**.
3.  **Cost**: ~250 x L4 GPUs.

## Autoscaling Behavior (DWS)
**Critical**: The current cluster uses **Dynamic Workload Scheduler (DWS)** with `queued_provisioning` enabled.
-   **Atomic Scaling**: Nodes do **NOT** scale incrementally (1, 2, 3...). 
-   **Behavior**: When a job requests 10 GPUs (e.g., specific replica count), DWS reserves **ALL 10 nodes together**. They come online as a single block. This prevents "partial scheduling" deadlocks where a job needing 10 GPUs gets stuck holding 3.


> **Note:** Testing via `kubectl port-forward` is strictly limited to low concurrency (<10 users) due to local tunnel bandwidth limits. Production traffic MUST use the Load Balancer.
