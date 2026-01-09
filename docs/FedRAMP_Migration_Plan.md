# FedRAMP Medium Migration Plan

This document outlines the strategic roadmap for migrating the AI Inference Platform from the current Proof-of-Concept (PoC) environment to a **FedRAMP Medium** compliant production environment on Google Cloud.

## Phase 1: Foundation (Assured Workloads)

We cannot simply "upgrade" the existing project. We must establish a complaint landing zone.

1.  **Create Assured Workloads Folder**:
    *   Action: Provision a new Google Cloud Folder using the **"US Regions & Support"** (IL4/FedRAMP High) compliance regime.
    *   *Effect*: Automatically enforces Organization Policies (restricts regions to US-only, restrict support to US Persons).
2.  **New Project Provisioning**:
    *   Create a new project (e.g., `ai-platform-prod-fedramp`) *inside* this Assured Workload folder.
    *   This inherits all compliance guardrails immediately.

## Phase 2: Infrastructure Hardening (Terraform Updates)

The Terraform configuration requires specific modifications to meet FedRAMP controls (FIPS 140-2).

1.  **FIPS-Compliant Node Image**:
    *   Update `main.tf` node config to use a FIPS-validated OS image.
    *   *Change*: `image_type = "COS_CONTAINERD"` -> investigate/enable GKE FIPS mode (e.g., specific FIPS-enabled releases).
2.  **Shielded GKE Nodes**:
    *   Enforce `enable_shielded_nodes = true`.
    *   Enforce `enable_secure_boot = true`.
3.  **Strict Networking**:
    *   **No Public Endpoint**: The Control Plane must be `enable_private_endpoint = true`.
    *   **Bastion/IAP Access**: Operations team must access via Identity-Aware Proxy (IAP), not direct network connection.

## Phase 3: Trusted Software Supply Chain

FedRAMP requries strict control over *what* runs.

1.  **Artifact Registry (Private)**:
    *   Create a dedicated registry in the Assured project.
    *   Mirror the `gemma-3` model images and `ollama` base images into this registry.
    *   *Constraint*: Block all external pulls (Docker Hub, etc.) via Organization Policy.
2.  **Vulnerability Scanning**:
    *   Enable **On-Demand Scanning API**.
    *   Policy: Blocks deployment of any image with "Critical" or "High" CVEs.
3.  **Binary Authorization**:
    *   Implement "Attestor" workflow. Images must be signed by the CI/CD pipeline before GKE allows them to start.

## Phase 4: Migration & Cutover

1.  **Deploy Parallel Stack**:
    *   Run `terraform apply` targeting the new Assured Project.
2.  **Data Migration**:
    *   Since the model is stateless, no DB migration is needed.
    *   Verify Model Hash (SHA256) ensures the exact same weights are loaded.
3.  **Validation**:
    *   Run the "Compliance Verification Script" (verifies encryption keys, logging sinks, and FIPS checks).
4.  **DNS Cutover**:
    *   Update internal DNS to point to the new Internal Load Balancer (ILB).

## Summary of Changes

| Component | Current PoC | FedRAMP Target |
| :--- | :--- | :--- |
| **Project** | Standard | **Assured Workloads** |
| **Support** | Global | **US Person Only** |
| **Encryption** | Google Managed | **CMEK (Customer Managed Keys)** |
| **Images** | Public (GCR) | **Private + Signed (BinAuthz)** |
| **Access** | Public Endpoint | **Private Only (IAP)** |
