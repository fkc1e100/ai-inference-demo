provider "google" {
  project = "gca-gke-2025"
  region  = "us-east1"
}

# Stabilized & Hardened L4 Inference Cluster Archetype
resource "google_container_cluster" "ai_inference" {
  name                     = "ai-inference-demo-v1"
  location                 = "us-east1"
  remove_default_node_pool = true
  initial_node_count       = 1
  deletion_protection      = false
  network                  = "default"
  
  # Workload Identity is required for modern GKE security
  workload_identity_config { 
    workload_pool = "gca-gke-2025.svc.id.goog" 
  }

  # Hardened Master Security (Connect Gateway compatible)
  # For this demo, we can allow public access to make it easier for you to connect initially
  # but in production you would restrict this.
  master_authorized_networks_config {
    cidr_blocks {
      cidr_block   = "0.0.0.0/0"
      display_name = "Allow All (Demo Only)"
    }
  }

  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = false
    master_ipv4_cidr_block  = "172.16.0.48/28"
  }
}

# 1. System Node Pool: Dedicated to cluster services (kube-dns, etc)
resource "google_container_node_pool" "system_node_pool" {
  name       = "system-node-pool"
  location   = "us-east1"
  cluster    = google_container_cluster.ai_inference.name
  node_count = 1
  
  autoscaling {
    min_node_count = 1
    max_node_count = 3
  }
  
  node_config {
    machine_type = "e2-standard-4"
    oauth_scopes = ["https://www.googleapis.com/auth/cloud-platform"]
  }
}

# 2. GPU Workload Pool: Dedicated strictly to AI Inference
resource "google_container_node_pool" "gpu_node_pool" {
  name       = "l4-gpu-node-pool"
  location   = "us-east1"
  cluster    = google_container_cluster.ai_inference.name
  # node_count = 1 (Removed for Autoscaling)
  initial_node_count = 1
  
  autoscaling {
    min_node_count = 1
    max_node_count = 5
  }
  
  # We use explicit zones to ensure capacity
  node_locations = ["us-east1-b", "us-east1-c", "us-east1-d"]

  node_config {
    machine_type = "g2-standard-12"
    
    # Taint ensures only AI workloads run here
    taint {
      key    = "nvidia.com/gpu"
      value  = "present"
      effect = "NO_SCHEDULE"
    }
    
    guest_accelerator {
      type  = "nvidia-l4"
      count = 1
      gpu_driver_installation_config { 
        gpu_driver_version = "LATEST" 
      }
    }
    
    oauth_scopes = ["https://www.googleapis.com/auth/cloud-platform"]
  }
}
