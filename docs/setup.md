# Setup Guide

This document provides instructions for setting up the Kubernetes Playground project.

## Prerequisites

- Python 3.9 or higher (up to 3.14)
- Docker or Podman
- Kubernetes cluster (local or remote)
- kubectl CLI tool
- Helm (for chart deployments)
- VMware vCenter Server (for VMware integration features)

## Environment Setup

### Python Environment

1. Create a virtual environment:

   ```bash
   python -m venv .venv
   ```

2. Activate the virtual environment:

   ```bash
   source .venv/bin/activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. For development, install additional dependencies:

   ```bash
   pip install -r requirements-dev.txt
   ```

### Kubernetes Setup

1. Ensure your Kubernetes cluster is running and accessible:

   ```bash
   kubectl cluster-info
   ```

2. Create namespaces for the project:

   ```bash
   kubectl create namespace monitoring
   kubectl create namespace namespace-ops
   kubectl create namespace vmware-integration
   ```

3. Set up RBAC permissions for monitoring applications:

   ```bash
   kubectl apply -f deployments/monitoring/pod_monitor/rbac.yaml
   ```

## Docker/Podman Setup

For building container images:

1. Build the Pod Monitor image:

   ```bash
   podman build -t k8s-playground/pod-monitor:latest ./apps/monitoring/pod_monitor
   ```

2. Build the Cluster Monitor image:

   ```bash
   podman build -t k8s-playground/cluster-monitor:latest ./apps/monitoring/cluster_monitor
   ```

3. Run a container locally for testing:

   ```bash
   podman run -it --rm \
     -e KUBECONFIG=/tmp/kubeconfig \
     -v ~/.kube/config:/tmp/kubeconfig:ro \
     k8s-playground/pod-monitor:latest monitor --namespace default
   ```

## VMware Integration Setup

For applications that integrate with VMware:

1. Create a VMware credentials secret:

   ```bash
   # Create a .env.secret file with your VMware credentials
   echo "host=vcenter.example.com" > .env.secret
   echo "username=your-username" >> .env.secret
   echo "password=your-password" >> .env.secret
   
   # Apply the secret using kustomize
   kubectl apply -k deployments/monitoring/pod_monitor
   ```

2. Verify VMware connectivity:

   ```bash
   # Run the pod monitor with VMware integration enabled
   podman run -it --rm \
     -e KUBECONFIG=/tmp/kubeconfig \
     -e POD_MONITOR_VMWARE_HOST=vcenter.example.com \
     -e POD_MONITOR_VMWARE_USERNAME=your-username \
     -e POD_MONITOR_VMWARE_PASSWORD=your-password \
     -v ~/.kube/config:/tmp/kubeconfig:ro \
     k8s-playground/pod-monitor:latest monitor --log-level DEBUG
   ```

## Prometheus Integration

To set up Prometheus to scrape metrics from our applications:

1. Ensure Prometheus is installed in your cluster:

   ```bash
   # Using Helm
   helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
   helm repo update
   helm install prometheus prometheus-community/prometheus \
     --namespace monitoring \
     --set server.persistentVolume.enabled=false
   ```

2. Verify that Prometheus can discover our applications:

   ```bash
   # Port-forward to Prometheus UI
   kubectl port-forward -n monitoring svc/prometheus-server 9090:80
   ```

   Then visit [http://localhost:9090/targets](http://localhost:9090/targets) to confirm that the pod-monitor targets are being scraped.

## Development Tools Setup

1. Set up pre-commit hooks:

   ```bash
   pre-commit install
   ```

2. Configure your IDE to use the project's linting and formatting settings.

## Application Configuration

### Pod Monitor Configuration

The Pod Monitor application can be configured using environment variables or a ConfigMap:

1. Edit the ConfigMap to customize monitoring parameters:

   ```bash
   kubectl edit configmap pod-monitor-config -n monitoring
   ```

2. Key configuration parameters:

   - `namespaces`: Comma-separated list of namespaces to monitor
   - `pod_problematic_threshold`: Time in seconds before a non-Running pod is considered problematic
   - `monitoring_interval`: Interval in seconds between monitoring iterations
   - `prometheus_port`: Port to expose Prometheus metrics on
   - `log_level`: Logging level (INFO, DEBUG, WARNING, ERROR)

### Cluster Monitor Configuration

Similar to the Pod Monitor, the Cluster Monitor can be configured via ConfigMap:

1. Edit the ConfigMap:

   ```bash
   kubectl edit configmap cluster-monitor-config -n monitoring
   ```

2. Key configuration parameters:

   - `monitoring_interval`: Interval in seconds between monitoring iterations
   - `prometheus_port`: Port to expose Prometheus metrics on
   - `log_level`: Logging level

## Verification

To verify your setup:

1. Run the tests:

   ```bash
   pytest
   ```

2. Deploy the Pod Monitor application:

   ```bash
   kubectl apply -k deployments/monitoring/pod_monitor
   ```

3. Check the Pod Monitor logs:

   ```bash
   kubectl logs -n monitoring -l app=pod-monitor
   ```

4. Access the metrics endpoint:

   ```bash
   kubectl port-forward -n monitoring svc/pod-monitor 9090:9090
   curl http://localhost:9090/metrics
   ```
