# Kubernetes Playground

## Last Updated

March 19, 2025

A playground for Kubernetes applications focused on monitoring.

## Table of Contents

- [Project Overview](#project-overview)
- [Directory Structure](#directory-structure)
- [Quick Start](#quick-start)
  - [Prerequisites](#prerequisites)
  - [Deploying the Pod Monitor](#deploying-the-pod-monitor)
  - [Example: Monitoring Specific Namespaces](#example-monitoring-specific-namespaces)
- [Documentation](#documentation)
- [Features and Status](#features-and-status)
  - [Monitoring Applications](#monitoring-applications)
    - [Pod Monitor](#pod-monitor-implemented-v100)
    - [Cluster Monitor](#cluster-monitor-implemented-v100)
- [Contributing](#contributing)
- [License](#license)

## Project Overview

This project serves as a playground for building and testing Kubernetes applications with a focus on monitoring capabilities. It provides a comprehensive set of tools for monitoring Kubernetes resources and integrating with VMware infrastructure to correlate pod failures with underlying infrastructure issues.

## Directory Structure

```bash
k8s_playground/
├── apps/                     # Application code
│   ├── monitoring/           # Monitoring applications
│   │   ├── cluster_monitor/  # Cluster-level monitoring
│   │   └── pod_monitor/      # Pod-level monitoring
├── deployments/              # Kubernetes manifests
│   ├── monitoring/
├── docs/                     # Documentation
├── infrastructure/           # Infrastructure as code
├── scripts/                  # Utility scripts
├── tests/                    # Test suite
└── tools/                    # Development tools
```

## Quick Start

### Prerequisites

- Kubernetes cluster (v1.19+)
- kubectl configured to access your cluster
- Docker or Podman for building container images
- For VMware integration: Access to VMware vCenter/ESXi

### Deploying the Pod Monitor

1. Create the monitoring namespace:

    ```bash
    kubectl create namespace monitoring
    ```

2. Deploy the Pod Monitor:

    ```bash
    # Deploy RBAC resources
    kubectl apply -f deployments/monitoring/pod_monitor/rbac.yaml
    
    # Deploy ConfigMap
    kubectl apply -f deployments/monitoring/pod_monitor/configmap.yaml
    
    # Deploy the application
    kubectl apply -f deployments/monitoring/pod_monitor/deployment.yaml
    
    # Deploy the service for Prometheus metrics
    kubectl apply -f deployments/monitoring/pod_monitor/service.yaml
    ```

3. For VMware integration, create the required secret:

    ```bash
    kubectl create secret generic pod-monitor-vmware-credentials \
      --from-literal=host=vcenter.example.com \
      --from-literal=username=your-vmware-username \
      --from-literal=password=your-vmware-password \
      -n monitoring
    ```

4. Label your Kubernetes nodes with their corresponding VMware VM names:

    ```bash
    kubectl label node worker-1 vm-name=worker-1-vm
    ```

### Example: Monitoring Specific Namespaces

To monitor only specific namespaces with critical applications:

1. Update the ConfigMap:

    ```yaml
    cat <<EOF | kubectl apply -f -
    apiVersion: v1
    kind: ConfigMap
    metadata:
      name: pod-monitor-config
      namespace: monitoring
    data:
      config.yaml: |
        namespaces:
          - production
          - kube-system
        pod_label_selectors:
          app: critical
        monitoring_interval: 30
    EOF
    ```

2. Restart the Pod Monitor:

    ```bash
    kubectl rollout restart deployment pod-monitor -n monitoring
    ```

3. Check the logs to verify monitoring:

    ```bash
    kubectl logs -n monitoring -l app=pod-monitor
    ```

## Documentation

Detailed documentation is available in the `docs/` directory:

- [Setup Guide](docs/setup.md) - Instructions for setting up the project environment
- [Project Organization](docs/project_organization.md) - Overview of the project structure and organization
- [Development Guidelines](docs/development.md) - Development practices and guidelines
- [Deployment Guide](docs/deployment.md) - Detailed deployment instructions

Each documentation file includes navigation links to help you move between related topics. For application-specific documentation, see the README files in the respective application directories:

- [Monitoring Applications](apps/monitoring/README.md) - Documentation for monitoring applications

## Features and Status

### Monitoring Applications

#### Pod Monitor [IMPLEMENTED v1.0.0]

The Pod Monitor tracks the status of pods in specified namespaces and provides alerts for problematic pods. It also integrates with VMware to correlate pod issues with underlying infrastructure problems. This also includes VM power state monitoring, ESXi host status checking, datastore capacity monitoring, and VM-to-Node correlation.

**Key Features:**

- Pod status monitoring and alerting
- Node status monitoring and alerting
- VMware integration for infrastructure correlation
- Prometheus metrics exposure
- VM power state monitoring
- ESXi host status checking
- Datastore capacity monitoring
- VM-to-Node correlation

**Example Use Case:**

Monitoring critical application pods and correlating failures with VMware infrastructure issues:

```bash
# Deploy a sample application
kubectl create namespace sample-app
kubectl apply -f examples/sample-app.yaml

# Configure Pod Monitor to watch the sample-app namespace
kubectl patch configmap pod-monitor-config -n monitoring --type merge \
  -p '{"data":{"config.yaml":"namespaces:\n  - sample-app\nmonitoring_interval: 30"}}'

# Simulate a VM issue (in test environment)
# Then check the Pod Monitor logs to see the correlation
kubectl logs -n monitoring -l app=pod-monitor
```

#### Cluster Monitor [IMPLEMENTED v1.0.0]

The Cluster Monitor provides an overview of the Kubernetes cluster health, focusing on control plane components, resource usage, and overall cluster status.

**Key Features:**

- Control plane component monitoring
- Node resource usage tracking
- Cluster events monitoring
- Prometheus metrics exposure

## Contributing

Contributions are welcome! Please check the [Development Guidelines](docs/development.md) for more information on how to contribute to this project.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
