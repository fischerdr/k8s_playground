# Project Organization

This document outlines the organization and structure of the Kubernetes Playground project.

## Navigation

- [Main README](../README.md)
- [Documentation Index](index.md)
- [Setup Guide](setup.md)
- **Project Organization** (You are here)
- [Development Guidelines](development.md)
- [Deployment Guide](deployment.md)
- [VMware Integration Guide](vmware_integration.md)

## Table of Contents

- [Directory Structure](#directory-structure)
- [Application Structure](#application-structure)
- [Deployment Structure](#deployment-structure)
- [Feature Status](#feature-status)
- [Development Status](#development-status)
- [Implemented Applications](#implemented-applications)
  - [Pod Monitor](#pod-monitor)
  - [Cluster Monitor](#cluster-monitor)
- [Development Workflow](#development-workflow)
- [Prometheus Integration](#prometheus-integration)
- [VMware Integration](#vmware-integration)
  - [VMware Features](#vmware-features)

## Last Updated

March 19, 2025

## Directory Structure

```bash
k8s_playground/
├── apps/                     # Application code
│   └── monitoring/           # Monitoring applications
│       ├── cluster_monitor/  # Cluster-level monitoring
│       └── pod_monitor/      # Pod-level monitoring
├── deployments/              # Kubernetes manifests
│   └── monitoring/
│       ├── cluster_monitor/  # Cluster monitor deployment
│       └── pod_monitor/      # Pod monitor deployment
├── docs/                     # Documentation
├── infrastructure/           # Infrastructure as code
│   ├── helm/                 # Helm charts
│   └── terraform/            # Terraform configurations
├── scripts/                  # Utility scripts
├── tests/                    # Test suite
│   ├── unit/                 # Unit tests
│   ├── integration/          # Integration tests
│   └── e2e/                  # End-to-end tests
└── tools/                    # Development tools
```

## Application Structure

Each application in the `apps/` directory follows this structure:

```bash
app_name/
├── __init__.py
├── main.py              # Application entry point
├── models/              # Data models
│   └── metrics.py       # Metric definitions for monitoring apps
├── services/            # Business logic
│   ├── kubernetes_service.py  # K8s API interactions
│   └── prometheus_service.py  # Prometheus metrics exposure
├── controllers/         # Request handlers
├── utils/               # Utility functions
├── config/              # Configuration handling
│   └── settings.py      # Application settings
└── requirements.txt     # Application dependencies
```

## Deployment Structure

Each application in the `deployments/` directory follows this structure:

```bash
app_name/
├── base/                # Base Kustomize resources
│   ├── deployment.yaml  # Deployment definition
│   ├── service.yaml     # Service definition
│   ├── configmap.yaml   # ConfigMap for configuration
│   ├── rbac.yaml        # RBAC resources
│   └── kustomization.yaml
└── overlays/            # Environment-specific overlays
    ├── development/     # Development environment
    │   └── kustomization.yaml
    └── production/      # Production environment
        └── kustomization.yaml
```

## Feature Status

The following tables provide a comprehensive overview of all features in the Kubernetes Playground project, their implementation status, and version information.

### Monitoring Features

| Feature | Component | Description | Status | Version | Notes |
|---------|-----------|-------------|--------|---------|-------|
| Pod Status Monitoring | Pod Monitor | Monitors pod states in specific namespaces | [IMPLEMENTED] | v1.0.0 | Core functionality |
| Node Status Monitoring | Pod Monitor | Monitors node status | [IMPLEMENTED] | v1.0.0 | Core functionality |
| Cluster Health Monitoring | Cluster Monitor | Monitors overall cluster health | [IMPLEMENTED] | v1.0.0 | Core functionality |
| Prometheus Metrics | Pod Monitor | Exposes metrics to Prometheus | [IMPLEMENTED] | v1.0.0 | Core functionality |
| Alerting | Pod Monitor | Sends alerts for critical issues | [IMPLEMENTED] | v1.0.0 | Core functionality |

### VMware Integration Features

| Feature | Component | Description | Status | Version | Notes |
|---------|-----------|-------------|--------|---------|-------|
| VM Power State Monitoring | Pod Monitor | Checks VM power state | [IMPLEMENTED] | v1.0.0 | See [VMware Integration Guide](vmware_integration.md) |
| ESXi Host Monitoring | Pod Monitor | Monitors ESXi host status | [IMPLEMENTED] | v1.0.0 | See [VMware Integration Guide](vmware_integration.md) |
| Datastore Monitoring | Pod Monitor | Monitors datastore status and capacity | [IMPLEMENTED] | v1.0.0 | See [VMware Integration Guide](vmware_integration.md) |
| VM-to-Node Correlation | Pod Monitor | Maps K8s nodes to VMware VMs | [IMPLEMENTED] | v1.0.0 | See [VMware Integration Guide](vmware_integration.md) |

### Deployment Features

| Feature | Component | Description | Status | Version | Notes |
|---------|-----------|-------------|--------|---------|-------|
| Kubernetes Manifests | Deployment | YAML manifests for K8s deployment | [IMPLEMENTED] | v1.0.0 | See [Deployment Guide](deployment.md) |
| Helm Charts | Deployment | Helm charts for easy deployment | [PLANNED] | v1.1.0 | In development |
| Operator | Deployment | Kubernetes operator for management | [PLANNED] | v2.0.0 | Design phase |

### Cross-Namespace Operations

| Feature | Component | Description | Status | Version | Notes |
|---------|-----------|-------------|--------|---------|-------|
| Resource Synchronization | Namespace Ops | Syncs resources across namespaces | [PLANNED] | v1.2.0 | Design phase |
| Secret Sharing | Namespace Ops | Securely shares secrets | [PLANNED] | v1.2.0 | Design phase |

### Security Features

| Feature | Component | Description | Status | Version | Notes |
|---------|-----------|-------------|--------|---------|-------|
| RBAC Integration | All | Role-based access control | [IMPLEMENTED] | v1.0.0 | Core functionality |
| Secret Management | All | Secure handling of credentials | [IMPLEMENTED] | v1.0.0 | Core functionality |

### Observability Features

| Feature | Component | Description | Status | Version | Notes |
|---------|-----------|-------------|--------|---------|-------|
| Logging | All | Structured logging | [IMPLEMENTED] | v1.0.0 | Core functionality |
| Tracing | All | Distributed tracing | [PLANNED] | v1.1.0 | In development |
| Metrics | All | Performance and health metrics | [IMPLEMENTED] | v1.0.0 | Core functionality |

### Version History

| Version | Release Date | Major Features |
|---------|--------------|---------------|
| v1.0.0 | 2025-01-15 | Initial release with Pod Monitor, Cluster Monitor, and VMware integration |
| v1.1.0 | 2025-06-30 (planned) | Helm charts, distributed tracing, enhanced metrics |
| v1.2.0 | 2025-09-30 (planned) | Cross-namespace operations |
| v2.0.0 | 2026-01-15 (planned) | Kubernetes operator |

## Development Status

- **Current Version**: v1.0.0
- **Next Planned Release**: v1.1.0 (Expected: Q2 2025)

For detailed information about specific components, please refer to their respective documentation:

- [Development Guidelines](development.md)
- [Deployment Guide](deployment.md)

## Implemented Applications

### Pod Monitor

The Pod Monitor application monitors the state of pods in specified namespaces and provides the following features:

- Monitors pod status and reports alerts for problematic states [IMPLEMENTED v1.0.0]
- Tracks node status and reports alerts for nodes not in Ready state [IMPLEMENTED v1.0.0]
- Exposes metrics to Prometheus via a /metrics endpoint [IMPLEMENTED v1.0.0]
- Configurable via environment variables or ConfigMap [IMPLEMENTED v1.0.0]

### Cluster Monitor

The Cluster Monitor application provides overall Kubernetes cluster health monitoring:

- Tracks cluster-wide resource usage [IMPLEMENTED v1.0.0]
- Monitors control plane components [IMPLEMENTED v1.0.0]
- Alerts on cluster-level issues [IMPLEMENTED v1.0.0]
- Exposes metrics to Prometheus [IMPLEMENTED v1.0.0]

## Development Workflow

1. Create a new application in the appropriate domain directory
2. Develop and test locally using the virtual environment
3. Create deployment manifests in the corresponding deployments directory
4. Test deployment in a local Kubernetes cluster
5. Document the application in the docs directory

## Prometheus Integration

All monitoring applications expose metrics following these conventions:

- Metrics endpoint: `/metrics` [IMPLEMENTED v1.0.0]
- Port: 9090 [IMPLEMENTED v1.0.0]
- Metric naming: `k8s_<resource>_<metric>` [IMPLEMENTED v1.0.0]
- Common labels: `namespace`, `name`, `status` [IMPLEMENTED v1.0.0]

## VMware Integration

Applications that integrate with VMware follow these patterns:

- Use pyvmomi for VMware API interactions [IMPLEMENTED v1.0.0]
- Secure credential storage in Kubernetes Secrets [IMPLEMENTED v1.0.0]
- Correlation between Kubernetes nodes and VMware VMs [IMPLEMENTED v1.0.0]

### VMware Features

- VM power state monitoring [IMPLEMENTED v1.0.0]
- ESXi host status checking [IMPLEMENTED v1.0.0]
- Datastore capacity monitoring [IMPLEMENTED v1.0.0]
- VM resource usage monitoring (CPU, memory) [IMPLEMENTED v1.0.0]
