# AI Inference Platform (Demo)

This repository contains the Infrastructure-as-Code (Terraform) and Application Deployment (Helm) for the AI Inference Platform.

## Architecture

```mermaid
graph TD
    User[User / Application] -->|HTTP Request| LB[Load Balancer / Service]
    
    subgraph "GKE Cluster (ai-inference-demo-v1)"
        LB --> Pod[AI Inference Pod]
        
        subgraph "GPU Node Pool (Autoscaling 1-5)"
            Pod -->|Runs On| GPU[NVIDIA L4 GPU]
            Pod -->|Loads| Model[Gemma 3 Model]
        end
        
        subgraph "System Node Pool"
            Logs[Logging Agent]
            DNS[Kube DNS]
        end
    end
    
    Pod -.->|Auth| WI[Workload Identity]
    WI -.->|IAM| GCR[Artifact Registry]
    GCR -->|Pulls Image| Pod
```

## Quick Start

### Prerequisites
*   Google Cloud Project (Authenticated)
*   Terraform installed
*   Helm installed

### 1. Build Infrastructure
```bash
cd terraform
terraform init
terraform apply
```

### 2. Deploy Model
```bash
# Connect to cluster
gcloud container clusters get-credentials ai-inference-demo-v1 --region us-east1

# Install Chart
helm install ai-inference ./helm/ai-inference
```

### 3. Test
```bash
# Verify Pods
kubectl get pods

# Test Endpoint (Internal)
kubectl run curl-test --image=curlimages/curl --restart=Never --command -- sleep infinity
kubectl exec curl-test -- curl http://ai-inference:8000/
```
