# AI Inference Platform Proposal

## Executive Summary
This document outlines the architecture for incorporating AI assistance into the application. We propose a **Self-Hosted** approach using Google Kubernetes Engine (GKE) to host the **Gemma 3 (4B)** open model. This provides full data control, lower latency, and predictable scaling compared to managed APIs.

## 1. Architecture Overview

We utilize a "Google Cloud Native" stack to ensure reliability and security.

### Infrastructure (Terraform)
*   **Cluster**: `ai-inference-demo-v1` (Regional Resource in `us-east1`).
*   **Compute Engine**:
    *   **System Pool**: Isolated generic CPUs (`e2-standard-4`) for cluster management and logging.
    *   **Accelerator Pool**: Specialized GPU Nodes (`g2-standard-12` with NVIDIA L4) dedicated strictly to AI inference.

### Application Deployment (Helm)
*   **Model**: Google Gemma 3 4B (Instruction Tuned).
*   **Serving Engine**: Ollama (Optimized for low-latency inference).
*   **User Interface**: Streamlit Web Application (Chat Interface) for demonstration and interaction.
*   **Distribution**: Packaged as a standard Helm Chart (`ai-inference/`) for easy versioning and rollback.

## 2. Scalability Strategy (1000+ Users)

To handle burst traffic (e.g., 1000 users interacting simultaneously), we have implemented **Multi-Layer Autoscaling**:

1.  **Infrastructure Scaling (Cluster Autoscaler)**:
    *   The GPU Node Pool is configured to automatically scale from **1 to 5 nodes** based on demand.
    *   *Trigger*: When the "Queue" of requests fills up the current GPU, GKE requests a new node.
    *   *Time-to-Ready*: ~2-3 minutes for new hardware to come online.

2.  **Workload Scaling (HPA - Future Phase)**:
    *   Kubernetes monitors the "Inference Latency" or "GPU Utilization".
    *   Automatically adds more Pods (replicas) to fill the new nodes.

## 3. Security & Governance

We adhere to the "Secure by Design" principles:

*   **Identity First**: We leverage **Workload Identity Federation**. The AI Pods authenticate to Google Cloud (e.g., to pull models) using their Kubernetes Service Account. **No static keys or secrets** are stored in the cluster.
*   **Network Isolation**:
    *   **Private Nodes**: All compute nodes have only private IP addresses; they are not directly exposed to the public internet.
    *   **Control Plane**: Secured via standard GKE RBAC (Role Based Access Control).
*   **Data Privacy**:
    *   The model runs entirely within your VPC.
    *   User data sent to the model **never leaves your defined boundary** and is **not used for training** public models.

## 4. Operational Cost Estimation (Draft)

| Component | SKU | Estimated Cost (Hourly) | Notes |
| :--- | :--- | :--- | :--- |
| **Idle** (1 GPU) | 1x L4 GPU + 1x System Node | ~$0.85/hr | Minimum monthly run rate. |
| **Peak** (5 GPUs) | 5x L4 GPU + 1x System Node | ~$3.50/hr | Cost only during active scaling events. |

## 5. Next Steps for Production

1.  **Ingress Controller**: Setup an HTTPS Load Balancer with IAP (Identity Aware Proxy) to allow secure access for the App Team.
2.  **Observability**: Enable Google Cloud Managed Prometheus to track "Tokens Per Second" (TPS) and Latency.
