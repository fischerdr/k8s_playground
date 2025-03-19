# Deployment Guide for Kubernetes Playground

This document provides detailed instructions for deploying the Kubernetes Playground components to a Kubernetes cluster, with a focus on the monitoring applications.

## Table of Contents

- [Deployment Guide for Kubernetes Playground](#deployment-guide-for-kubernetes-playground)
  - [Table of Contents](#table-of-contents)
  - [Prerequisites](#prerequisites)
  - [Deployment Overview](#deployment-overview)
  - [Pod Monitor Deployment](#pod-monitor-deployment)
    - [Building the Image](#building-the-image)
    - [Deployment Steps](#deployment-steps)
    - [Configuration Options](#configuration-options)
      - [Kubernetes Configuration](#kubernetes-configuration)
      - [Pod Selection Configuration](#pod-selection-configuration)
      - [Monitoring Configuration](#monitoring-configuration)
      - [VMware Configuration](#vmware-configuration)
    - [Targeted Monitoring Setup](#targeted-monitoring-setup)
      - [1. Using ConfigMap](#1-using-configmap)
      - [2. Using Environment Variables](#2-using-environment-variables)
    - [VMware Integration](#vmware-integration)
    - [Production-Ready Features](#production-ready-features)
      - [High Availability](#high-availability)
      - [Security](#security)
      - [Observability](#observability)
      - [Resource Management](#resource-management)
  - [Cluster Monitor Deployment](#cluster-monitor-deployment)
  - [Troubleshooting](#troubleshooting)
    - [Common Issues](#common-issues)
    - [Logs and Debugging](#logs-and-debugging)

## Prerequisites

Before deploying the Kubernetes Playground components, ensure you have:

- A running Kubernetes cluster (v1.19+)
- `kubectl` CLI tool configured to access your cluster
- Necessary RBAC permissions to create resources in the target namespaces
- Docker or Podman for building container images (if deploying from source)
- For VMware integration: Access to a VMware vCenter Server or ESXi host

## Deployment Overview

The Kubernetes Playground project consists of several components that can be deployed independently:

1. **Pod Monitor**: Monitors pod states in specific namespaces
2. **Cluster Monitor**: Monitors overall Kubernetes cluster health
3. **Namespace Operations**: Tools for cross-namespace operations

Each component has its own deployment configuration in the `deployments/` directory.

## Pod Monitor Deployment

The Pod Monitor is a critical component that monitors pod states in specific namespaces and can integrate with VMware infrastructure to provide comprehensive monitoring.

### Building the Image

If you need to build the Pod Monitor image locally:

```bash
# From the project root
cd apps/monitoring/pod_monitor
docker build -t k8s-playground/pod-monitor:latest .
```

### Deployment Steps

1. Create the monitoring namespace (if it doesn't exist):

    ```bash
    kubectl create namespace monitoring
    ```

2. Deploy the RBAC resources:

    ```bash
    kubectl apply -f deployments/monitoring/pod_monitor/rbac.yaml
    ```

3. Create the ConfigMap with your desired configuration:

    ```bash
    kubectl apply -f deployments/monitoring/pod_monitor/configmap.yaml
    ```

4. If using VMware integration, create the secrets:

    ```bash
    kubectl create secret generic pod-monitor-vmware-credentials \
    --from-literal=host=vcenter.example.com \
    --from-literal=username=your-vmware-username \
    --from-literal=password=your-vmware-password \
    -n monitoring
    ```

5. Deploy the Pod Monitor:

    ```bash
    kubectl apply -f deployments/monitoring/pod_monitor/deployment.yaml
    ```

6. Deploy the service (for Prometheus metrics):

    ```bash
    kubectl apply -f deployments/monitoring/pod_monitor/service.yaml
    ```

7. Deploy the PodDisruptionBudget for high availability:

    ```bash
    kubectl apply -f deployments/monitoring/pod_monitor/pdb.yaml
    ```

8. Deploy the NetworkPolicy for enhanced security:

    ```bash
    kubectl apply -f deployments/monitoring/pod_monitor/network-policy.yaml
    ```

Alternatively, you can use Kustomize to deploy all resources at once:

```bash
# For production environment
kubectl apply -k deployments/monitoring/pod_monitor/overlays/production

# For development environment
kubectl apply -k deployments/monitoring/pod_monitor/overlays/development
```

### Configuration Options

The Pod Monitor can be configured through the ConfigMap. Here are the key configuration options:

#### Kubernetes Configuration

| Option | Description | Default |
|--------|-------------|---------|
| `namespaces` | List of namespaces to monitor | `["default"]` |
| `kubeconfig_path` | Path to kubeconfig file (usually not needed in-cluster) | `None` |

#### Pod Selection Configuration

| Option | Description | Default |
|--------|-------------|---------|
| `pod_label_selectors` | Labels to filter which pods to monitor | `{}` |
| `monitor_all_nodes` | Whether to monitor all nodes or only those running selected pods | `false` |

#### Monitoring Configuration

| Option | Description | Default |
|--------|-------------|---------|
| `pod_problematic_threshold` | Time in seconds before a non-running pod is considered problematic | `300` |
| `monitoring_interval` | Monitoring interval in seconds | `60` |

#### VMware Configuration

| Option | Description | Default |
|--------|-------------|---------|
| `vmware.host` | VMware vCenter/ESXi host | Required if using VMware |
| `vmware.username` | VMware username | Required if using VMware |
| `vmware.password` | VMware password | Required if using VMware |
| `vmware.port` | VMware API port | `443` |
| `vmware.disable_ssl_verification` | Whether to disable SSL verification | `false` |

### Targeted Monitoring Setup

For large clusters with hundreds of nodes, it's recommended to use targeted monitoring to reduce the load on your VMware vCenter Server. This can be configured in two ways:

#### 1. Using ConfigMap

Edit the `configmap.yaml` file:

```yaml
data:
  config.yaml: |
    # Pod selection configuration
    pod_label_selectors:
      app: critical
      tier: production
    monitor_all_nodes: false
```

#### 2. Using Environment Variables

You can also configure these options via environment variables in the deployment:

```yaml
env:
- name: POD_MONITOR_POD_LABEL_SELECTORS
  value: "app=critical,tier=production"
- name: POD_MONITOR_MONITOR_ALL_NODES
  value: "false"
```

### VMware Integration

To enable VMware integration, you need to:

1. Create a secret with VMware credentials:

```bash
kubectl create secret generic pod-monitor-vmware-credentials \
  --from-literal=host=vcenter.example.com \
  --from-literal=username=your-vmware-username \
  --from-literal=password=your-vmware-password \
  -n monitoring
```

1. Label your Kubernetes nodes with their corresponding VMware VM names:

```bash
kubectl label node worker-1 vm-name=worker-1-vm
```

Note: If the `vm-name` label is not present, the system will use the node name as the VMware guest name.

### Production-Ready Features

The Pod Monitor includes several production-ready features to ensure reliability, security, and observability:

#### High Availability

- **Replicas**: The production deployment uses 3 replicas for high availability
- **Rolling Updates**: Configured with `maxSurge: 1` and `maxUnavailable: 0` for zero-downtime updates
- **PodDisruptionBudget**: Ensures at least one pod is always available during voluntary disruptions
- **Health Probes**: Includes liveness, readiness, and startup probes for better resilience

#### Security

- **RBAC**: Proper role-based access control with a dedicated ServiceAccount
- **SecurityContext**: Runs as non-root user with minimal capabilities
- **NetworkPolicy**: Restricts inbound and outbound traffic to only what's necessary
- **Secrets Management**: Sensitive credentials stored in Kubernetes Secrets

#### Observability

- **Prometheus Integration**: Exposes metrics for Prometheus scraping
- **Health Endpoints**: Provides `/health` endpoint for monitoring application health
- **Logging**: Configurable log levels with structured logging

#### Resource Management

- **Resource Limits**: Properly defined CPU and memory limits and requests
- **Environment-Specific Configurations**: Separate configurations for production and development
- **Kustomize Overlays**: Easy customization for different environments

## Cluster Monitor Deployment

The Cluster Monitor deployment follows a similar pattern to the Pod Monitor. Refer to the specific deployment files in `deployments/monitoring/cluster_monitor/` for details.

## Troubleshooting

### Common Issues

1. **Pod Monitor not starting**:
   - Check the pod logs: `kubectl logs -n monitoring -l app=pod-monitor`
   - Verify RBAC permissions are correct
   - Ensure the ConfigMap exists and has the correct format

2. **VMware integration not working**:
   - Verify VMware credentials in the secret
   - Check network connectivity from the pod to the VMware host
   - Ensure nodes are properly labeled with VM names

3. **Missing metrics in Prometheus**:
   - Verify the service is correctly exposing port 9090
   - Check that Prometheus is configured to scrape the pod-monitor endpoint
   - Verify the pod-monitor has the correct annotations for Prometheus discovery

4. **Health checks failing**:
   - Check the pod logs for any errors
   - Verify the application is properly initialized
   - Check if the `/health` endpoint is responding correctly

### Logs and Debugging

To increase log verbosity, update the ConfigMap:

```yaml
data:
  log_level: "DEBUG"
```

Or set the environment variable:

```yaml
env:
- name: POD_MONITOR_LOG_LEVEL
  value: "DEBUG"
```

For more detailed troubleshooting, refer to the [setup.md](setup.md) and [development.md](development.md) documents.
