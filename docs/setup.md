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

The VMware integration allows our monitoring applications to check the status of the VMware infrastructure that hosts our Kubernetes nodes. This is particularly useful for troubleshooting when pods aren't running properly.

### Purpose

- Check if the VMware guest that a Kubernetes node is running on is operational
- Verify if the ESXi host running the guest has any errors
- Monitor datastores assigned to VMs for events, alerts, and capacity issues
- Correlate pod failures with potential underlying VMware infrastructure issues

### VMware System Requirements

- VMware vCenter Server or ESXi host
- User account with read permissions to VMs, hosts, and datastores
- Network connectivity from the Kubernetes cluster to the VMware environment

### Configuration

1. Create a Kubernetes Secret with VMware credentials:

   ```bash
   kubectl create secret generic vmware-credentials \
     --from-literal=username=your-vmware-username \
     --from-literal=password=your-vmware-password \
     -n monitoring
   ```

2. Update the Pod Monitor ConfigMap with VMware connection details:

   ```bash
   kubectl apply -f - <<EOF
   apiVersion: v1
   kind: ConfigMap
   metadata:
     name: pod-monitor-config
     namespace: monitoring
   data:
     vmware.host: "vcenter.example.com"
     vmware.port: "443"
     vmware.disable_ssl_verification: "true"  # Set to false in production
     vmware.datastore.low_space_threshold: "10"  # Alert when less than 10% free space
     
     # Targeted monitoring configuration
     pod_label_selectors: "app=critical,tier=production"  # Only monitor pods with these labels
     monitor_all_nodes: "false"  # Set to true to monitor all nodes regardless of pod selection
   EOF
   ```

3. Kubernetes nodes can be labeled with their corresponding VMware VM names:

   ```bash
   # Example: Label a node with its VMware VM name
   kubectl label node worker-1 vm-name=worker-1-vm
   ```

   > **Note:** If the `vm-name` label is not present, the system will use the node name as the VMware guest name.

### Targeted Monitoring

To optimize vCenter performance in large clusters, the Pod Monitor supports targeted monitoring:

1. **Pod Label Selectors**: Only monitor pods (and their nodes) that match specific labels
   - Configure with comma-separated key=value pairs (e.g., `app=critical,tier=production`)
   - This significantly reduces the number of VMware API calls in large clusters

2. **Selective Node Monitoring**: By default, only nodes running the selected pods will be monitored
   - This prevents unnecessary VMware API calls for nodes not running critical workloads
   - Set `monitor_all_nodes: "true"` to monitor all nodes regardless of pod selection

3. **Environment Variables**: You can also configure these options via environment variables:
   - `POD_MONITOR_POD_LABEL_SELECTORS=app=critical,tier=production`
   - `POD_MONITOR_MONITOR_ALL_NODES=false`

This targeted approach is especially beneficial in large clusters with hundreds of nodes, as it minimizes the impact on your vCenter Server while still providing critical monitoring for your most important workloads.

### VMware Verification

To verify that the VMware integration is working:

1. Check the Pod Monitor logs for successful VMware connections:

   ```bash
   kubectl logs -f deployment/pod-monitor -n monitoring | grep VMware
   ```

2. Intentionally power off a VMware VM that hosts a Kubernetes node and verify that the Pod Monitor detects this:

   ```bash
   kubectl get nodes  # Check that the node is NotReady
   kubectl logs deployment/pod-monitor -n monitoring | grep "VMware machine"  # Should show alerts
   ```

3. Check for datastore monitoring:

   ```bash
   # View datastore-related alerts
   kubectl logs deployment/pod-monitor -n monitoring | grep "Datastore"
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
