# Kubernetes Playground

A playground project for developing and testing Kubernetes applications with Python, focusing on monitoring, cross-namespace operations, and VMware integration.

## Project Structure

```bash
k8s_playground/
├── apps/                      # Application code
│   ├── monitoring/            # Monitoring applications
│   │   ├── cluster_monitor/   # Cluster-wide monitoring
│   │   └── pod_monitor/       # Pod and node monitoring with VMware integration
│   ├── namespace_ops/         # Cross-namespace operations
│   └── vmware_integration/    # VMware integration applications
├── deployments/               # Kubernetes deployment manifests
│   ├── monitoring/
│   │   ├── cluster_monitor/   # Cluster monitor deployment
│   │   └── pod_monitor/       # Pod monitor deployment
│   ├── namespace_ops/
│   └── vmware_integration/
├── docs/                      # Documentation
├── infrastructure/            # Infrastructure as code
│   ├── helm/                  # Helm charts
│   └── terraform/             # Terraform configurations
├── scripts/                   # Utility scripts
├── tests/                     # Test suite
└── tools/                     # Development tools
```

## Getting Started

1. Clone the repository

2. Set up your Python virtual environment:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. For development, install additional dependencies:

   ```bash
   pip install -r requirements-dev.txt
   ```

## Applications

### Monitoring

Applications for monitoring Kubernetes clusters and workloads:

- **Pod Monitor**: Monitors pod states in specified namespaces, tracks node status, integrates with VMware, and exposes metrics to Prometheus.
- **Cluster Monitor**: Provides overall Kubernetes cluster health monitoring and exposes metrics to Prometheus.

Features include:

- Pod status monitoring and alerting
- Node status monitoring and alerting
- VMware machine integration
- Prometheus metrics exposure
- Configurable thresholds and namespaces

### Namespace Operations

Tools for working with and across Kubernetes namespaces.

### VMware Integration

Applications that integrate Kubernetes with VMware infrastructure.

## Deployment

Each application includes a complete set of Kubernetes manifests:

- Deployment/StatefulSet for high availability
- Service for exposing metrics
- ConfigMap for configuration
- Secret for sensitive data
- RBAC resources for proper permissions
- Kustomization for easy deployment

To deploy an application:

```bash
kubectl apply -k deployments/monitoring/pod_monitor
```

## Development

This project follows the development practices outlined in the `docs/` directory. See `docs/project_organization.md` for details on the project structure and organization.

## License

See the [LICENSE](LICENSE) file for details.
