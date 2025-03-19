# Deployment Guide for Kubernetes Playground

This document provides detailed instructions for deploying the Kubernetes Playground components to a Kubernetes cluster, with a focus on the monitoring applications.

## Navigation

- [Main README](../README.md)
- [Documentation Index](index.md)
- [Setup Guide](setup.md)
- [Project Organization](project_organization.md)
- [Development Guidelines](development.md)
- **Deployment Guide** (You are here)
- [VMware Integration Guide](vmware_integration.md)

## Table of Contents

- [Prerequisites](#prerequisites)
- [Deployment Overview](#deployment-overview)
- [Pod Monitor Deployment](#pod-monitor-deployment)
  - [Building the Image](#building-the-image)
  - [Deployment Steps](#deployment-steps)
  - [Configuration Options](#configuration-options)
    - [Kubernetes Configuration](#kubernetes-configuration)
    - [Pod Selection Configuration](#pod-selection-configuration)
    - [Monitoring Configuration](#monitoring-configuration)
- [Cluster Monitor Deployment](#cluster-monitor-deployment)
- [Prometheus Integration](#prometheus-integration)
- [Troubleshooting](#troubleshooting)
  - [Common Issues](#common-issues)
  - [Logs and Debugging](#logs-and-debugging)

## Last Updated

March 19, 2025

## Prerequisites

Before deploying the Kubernetes Playground components, ensure you have:

- Completed the [Setup Guide](setup.md)
- Access to a Kubernetes cluster with appropriate permissions
- kubectl CLI tool configured to access your cluster
- Docker/Podman for building container images (if deploying custom builds)

## Deployment Overview

The Kubernetes Playground project includes several deployable components:

1. **Pod Monitor**: Monitors pod states in specific namespaces
2. **Cluster Monitor**: Monitors overall cluster health
3. **VMware Integration**: Optional component for monitoring VMware infrastructure

Each component can be deployed independently or together, depending on your monitoring needs.

## Pod Monitor Deployment

### Building the Image

1. Build the Pod Monitor image:

   ```bash
   podman build -t k8s-playground/pod-monitor:latest ./apps/monitoring/pod_monitor
   ```

2. Push the image to your registry (if needed):

   ```bash
   podman push k8s-playground/pod-monitor:latest your-registry/k8s-playground/pod-monitor:latest
   ```

### Deployment Steps

1. Create the necessary RBAC resources:

   ```bash
   kubectl apply -f deployments/monitoring/pod_monitor/rbac.yaml
   ```

2. Create a ConfigMap for Pod Monitor configuration:

   ```bash
   kubectl apply -f deployments/monitoring/pod_monitor/configmap.yaml
   ```

3. Deploy the Pod Monitor:

   ```bash
   kubectl apply -f deployments/monitoring/pod_monitor/deployment.yaml
   ```

4. Verify the deployment:

   ```bash
   kubectl get pods -n monitoring -l app=pod-monitor
   kubectl logs -n monitoring -l app=pod-monitor
   ```

### Configuration Options

The Pod Monitor can be configured using a ConfigMap or environment variables.

#### Kubernetes Configuration

| Option | Description | Default | Environment Variable |
|--------|-------------|---------|---------------------|
| `namespaces` | Comma-separated list of namespaces to monitor | `default` | `POD_MONITOR_NAMESPACES` |
| `kube_config_path` | Path to kubeconfig file | In-cluster config | `KUBECONFIG` |
| `in_cluster` | Whether to use in-cluster config | `true` | `POD_MONITOR_IN_CLUSTER` |

#### Pod Selection Configuration

| Option | Description | Default | Environment Variable |
|--------|-------------|---------|---------------------|
| `pod_label_selectors` | Labels to filter which pods to monitor | `""` | `POD_MONITOR_POD_LABEL_SELECTORS` |
| `monitor_all_nodes` | Whether to monitor all nodes or only those running selected pods | `false` | `POD_MONITOR_MONITOR_ALL_NODES` |

#### Monitoring Configuration

| Option | Description | Default | Environment Variable |
|--------|-------------|---------|---------------------|
| `monitoring_interval` | Interval in seconds between monitoring iterations | `60` | `POD_MONITOR_INTERVAL` |
| `pod_problematic_threshold` | Time in seconds before a non-Running pod is considered problematic | `300` | `POD_MONITOR_POD_PROBLEMATIC_THRESHOLD` |
| `prometheus_port` | Port to expose Prometheus metrics on | `9090` | `POD_MONITOR_PROMETHEUS_PORT` |
| `log_level` | Logging level (INFO, DEBUG, WARNING, ERROR) | `INFO` | `POD_MONITOR_LOG_LEVEL` |

For VMware-specific configuration options, see the [VMware Integration Guide](vmware_integration.md).

## Cluster Monitor Deployment

1. Build the Cluster Monitor image:

   ```bash
   podman build -t k8s-playground/cluster-monitor:latest ./apps/monitoring/cluster_monitor
   ```

2. Create the necessary RBAC resources:

   ```bash
   kubectl apply -f deployments/monitoring/cluster_monitor/rbac.yaml
   ```

3. Create a ConfigMap for Cluster Monitor configuration:

   ```bash
   kubectl apply -f deployments/monitoring/cluster_monitor/configmap.yaml
   ```

4. Deploy the Cluster Monitor:

   ```bash
   kubectl apply -f deployments/monitoring/cluster_monitor/deployment.yaml
   ```

5. Verify the deployment:

   ```bash
   kubectl get pods -n monitoring -l app=cluster-monitor
   kubectl logs -n monitoring -l app=cluster-monitor
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

   Then visit [http://localhost:9090/targets](http://localhost:9090/targets) to confirm that the pod-monitor and cluster-monitor targets are being scraped.

3. Access the metrics endpoints directly:

   ```bash
   # Pod Monitor metrics
   kubectl port-forward -n monitoring svc/pod-monitor 9090:9090
   curl http://localhost:9090/metrics
   
   # Cluster Monitor metrics
   kubectl port-forward -n monitoring svc/cluster-monitor 9091:9091
   curl http://localhost:9091/metrics
   ```

## Troubleshooting

### Common Issues

1. **Pods not starting**:
   - Check for image pull errors: `kubectl describe pod -n monitoring <pod-name>`
   - Verify that the image is available in your registry
   - Check for RBAC issues in the pod logs

2. **No metrics being collected**:
   - Verify that the pod has the correct permissions
   - Check the pod logs for connection errors
   - Ensure the ConfigMap has the correct configuration

3. **VMware integration issues**:
   - See the [VMware Integration Guide](vmware_integration.md) for VMware-specific troubleshooting

### Logs and Debugging

1. View Pod Monitor logs:

   ```bash
   kubectl logs -f -n monitoring -l app=pod-monitor
   ```

2. View Cluster Monitor logs:

   ```bash
   kubectl logs -f -n monitoring -l app=cluster-monitor
   ```

3. Increase log verbosity by setting `log_level: "DEBUG"` in the ConfigMap or using the environment variable `POD_MONITOR_LOG_LEVEL=DEBUG`.
