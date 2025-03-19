# Project Organization

This document outlines the organization and structure of the Kubernetes Playground project.

## Directory Structure

- **apps/**: Contains the application code organized by domain
  - **monitoring/**: Applications for monitoring Kubernetes resources
    - **cluster_monitor/**: Monitors overall Kubernetes cluster health
    - **pod_monitor/**: Monitors pod states, node status, and VMware integration

- **deployments/**: Contains Kubernetes manifests for deploying applications
  - **monitoring/**: YAML files for monitoring applications
    - **cluster_monitor/**: Deployment manifests for cluster monitor
    - **pod_monitor/**: Deployment manifests for pod monitor

- **docs/**: Project documentation
  - **setup.md**: Setup instructions
  - **development.md**: Development guidelines
  - **deployment.md**: Deployment instructions
  - **api/**: API documentation

- **infrastructure/**: Infrastructure as code
  - **helm/**: Helm charts for deployments
  - **terraform/**: Terraform configurations for infrastructure provisioning

- **scripts/**: Utility scripts for development, deployment, and maintenance

- **tests/**: Test suite organized by application domain
  - **unit/**: Unit tests
  - **integration/**: Integration tests
  - **e2e/**: End-to-end tests

- **tools/**: Development tools and utilities

## Application Structure

Each application in the `apps/` directory follows this structure:

```text
app_name/
├── __init__.py
├── main.py              # Application entry point
├── models/              # Data models
│   └── metrics.py       # Metric definitions for monitoring apps
├── services/            # Business logic
│   ├── kubernetes_service.py  # K8s API interactions
│   ├── prometheus_service.py  # Prometheus metrics exposure
│   └── vmware_service.py      # VMware API interactions
├── utils/               # Utility functions
│   └── config.py        # Configuration utilities
├── Dockerfile           # Container definition
└── requirements.txt     # Python dependencies
```

## Deployment Structure

Each deployment in the `deployments/` directory includes:

```text
app_name/
├── deployment.yaml      # Kubernetes Deployment
├── service.yaml         # Kubernetes Service
├── configmap.yaml       # ConfigMap for configuration
├── secret.yaml          # Secret for sensitive data
├── rbac.yaml            # RBAC configuration
└── kustomization.yaml   # Kustomize configuration
```

## Implemented Applications

### Pod Monitor

The Pod Monitor application monitors the state of pods in specified namespaces and provides the following features:

- Monitors pod status and reports alerts for problematic states
- Tracks node status and reports alerts for nodes not in Ready state
- Integrates with VMware to correlate nodes with underlying VMs
- Exposes metrics to Prometheus via a /metrics endpoint
- Configurable via environment variables or ConfigMap

### Cluster Monitor

The Cluster Monitor application provides overall Kubernetes cluster health monitoring:

- Tracks cluster-wide resource usage
- Monitors control plane components
- Alerts on cluster-level issues
- Exposes metrics to Prometheus

## Development Workflow

1. Create a new application in the appropriate domain directory
2. Develop and test locally using the virtual environment
3. Create deployment manifests in the corresponding deployments directory
4. Test deployment in a local Kubernetes cluster
5. Document the application in the docs directory

## Prometheus Integration

All monitoring applications expose metrics following these conventions:

- Metrics endpoint: `/metrics`
- Port: 9090
- Metric naming: `k8s_<resource>_<metric>`
- Common labels: `namespace`, `name`, `status`

## VMware Integration

Applications that integrate with VMware follow these patterns:

- Use pyvmomi for VMware API interactions
- Secure credential storage in Kubernetes Secrets
- Correlation between Kubernetes nodes and VMware VMs
