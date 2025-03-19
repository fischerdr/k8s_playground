# Kubernetes Monitoring Applications

This directory contains applications for monitoring Kubernetes clusters and workloads.

## Applications

- **cluster_monitor**: Monitors overall Kubernetes cluster resources and health, exposing metrics to Prometheus for alerting and visualization.

- **pod_monitor**: Tracks pod and node status across specified namespaces with comprehensive VMware infrastructure monitoring:
  - Pod status monitoring and alerting
  - Node status monitoring and alerting
  - VMware guest machine status monitoring
  - ESXi host health monitoring
  - Datastore status and capacity monitoring
  - Prometheus metrics exposure

## VMware Integration

The pod_monitor application includes robust VMware infrastructure monitoring capabilities:

### Key Features

- **VM Status Monitoring**: Checks if VMware guests that Kubernetes nodes are running on are operational
- **ESXi Host Monitoring**: Verifies if ESXi hosts running the guests have any errors or alerts
- **Datastore Monitoring**: Checks datastores assigned to VMs for:
  - Overall health status
  - Triggered events and alerts
  - Capacity issues (configurable threshold for low space warnings)
- **Correlation**: Links pod failures with potential underlying VMware infrastructure issues

### When Monitoring Occurs

VMware infrastructure checks are triggered when:

- A pod is not running properly
- A VM is in a problematic state (powered off, suspended, etc.)

This focused approach ensures that VMware monitoring is performed specifically when troubleshooting is needed, providing valuable correlation between pod failures and potential infrastructure issues.

## Development

Follow the project development guidelines in the `docs/` directory, particularly:

- `docs/development.md` for development practices
- `docs/setup.md` for configuration and deployment instructions

## Deployment

Deployment manifests for these applications can be found in the `deployments/monitoring/` directory.
