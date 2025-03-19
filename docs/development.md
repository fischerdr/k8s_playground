# Development Guidelines

This document outlines the development practices for the Kubernetes Playground project.

## Navigation

- [Main README](../README.md)
- [Setup Guide](setup.md)
- [Project Organization](project_organization.md)
- **Development Guidelines** (You are here)
- [Deployment Guide](deployment.md)

## Table of Contents

- [Code Style](#code-style)
- [Development Environment](#development-environment)
- [Development Workflow](#development-workflow)
- [Python Best Practices](#python-best-practices)
- [Application Structure](#application-structure)
- [Monitoring Application Development](#monitoring-application-development)
  - [VMware Monitoring Development](#vmware-monitoring-development)
- [Prometheus Integration](#prometheus-integration)
- [Testing](#testing)
  - [Testing Monitoring Applications](#testing-monitoring-applications)
- [Container Development](#container-development)
- [Kubernetes Development](#kubernetes-development)
  - [Kubernetes Deployment Manifests](#kubernetes-deployment-manifests)

## Last Updated

March 19, 2025

## Code Style

- Follow PEP8 style guide for Python code
- Use Black for code formatting with a line length of 100 characters
- Use isort for import sorting
- Use flake8 for code linting
- Use type hints consistently throughout the codebase
- Use docstrings for all modules, classes, and functions

## Development Environment

- Use Python 3.9 minimum and 3.14 maximum
- Set up a virtual environment in `.venv/` directory:

  ```bash
  python -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  pip install -r requirements-dev.txt
  ```

- Configure pre-commit hooks to enforce code style:

  ```bash
  pre-commit install
  ```

## Development Workflow

1. Create a feature branch from the main branch
2. Implement the feature or fix
3. Write tests for your code
4. Run linting and formatting checks
5. Submit a pull request

## Python Best Practices

- Use virtual environments for development
- Use `rich` for console output
- Write modular code with clear separation of concerns
- Implement proper error handling and logging
- Use type hints consistently
- Add comprehensive docstrings to modules, classes, and functions
- Use `typer` for command-line interfaces

## Application Structure

Follow the standard application structure as outlined in `project_organization.md`:

```bash
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

## Monitoring Application Development

When developing monitoring applications:

1. **Service Separation**: Maintain clear separation between:
   - Kubernetes monitoring logic [IMPLEMENTED v1.0.0]
   - VMware integration logic [IMPLEMENTED v1.0.0]
   - Prometheus metrics exposure [IMPLEMENTED v1.0.0]

2. **Metric Naming Conventions**:
   - Use `k8s_<resource>_<metric>` format for Kubernetes metrics [IMPLEMENTED v1.0.0]
   - Use `vmware_<resource>_<metric>` format for VMware metrics [IMPLEMENTED v1.0.0]
   - Include relevant labels: namespace, name, status, etc. [IMPLEMENTED v1.0.0]

3. **Alert Generation**:
   - Define clear thresholds for alerting [IMPLEMENTED v1.0.0]
   - Implement rate limiting to prevent alert storms [IMPLEMENTED v1.0.0]
   - Log alerts with appropriate severity levels [IMPLEMENTED v1.0.0]

4. **Configuration Management**:
   - Make all thresholds and intervals configurable [IMPLEMENTED v1.0.0]
   - Support both environment variables and ConfigMap for configuration [IMPLEMENTED v1.0.0]
   - Provide sensible defaults [IMPLEMENTED v1.0.0]

### VMware Monitoring Development

When VMware check is enabled Monitoring

1. **Purpose and Scope**:
   - The primary purpose is to check if the VMware guest that a Kubernetes node is running on is operational [IMPLEMENTED v1.0.0]
   - Verify if the ESXi host running the guest has any errors [IMPLEMENTED v1.0.0]
   - Check datastores assigned to VMs for events, alerts, and capacity issues [IMPLEMENTED v1.0.0]
   - These checks are particularly important when troubleshooting non-running pods [IMPLEMENTED v1.0.0]
   - Focus on correlation between pod failures and underlying VMware infrastructure issues [IMPLEMENTED v1.0.0]

2. **Connection Management**:
   - Implement connection pooling to minimize connection overhead [IMPLEMENTED v1.0.0]
   - Handle connection failures gracefully [IMPLEMENTED v1.0.0]
   - Implement proper authentication [IMPLEMENTED v1.0.0]

3. **VM Correlation**:
   - Establish reliable mapping between Kubernetes nodes and VMware VMs [IMPLEMENTED v1.0.0]
   - Handle cases where correlation is not possible [IMPLEMENTED v1.0.0]
   - Document correlation methods [IMPLEMENTED v1.0.0]

4. **Datastore Monitoring**:
   - Check datastore health and status when VMs are in problematic states [IMPLEMENTED v1.0.0]
   - Monitor datastore capacity and alert on low free space [IMPLEMENTED v1.0.0]
   - Track datastore-related events and alarms [IMPLEMENTED v1.0.0]
   - Correlate datastore issues with VM and pod failures [IMPLEMENTED v1.0.0]

5. **Security Considerations**:
   - Never hardcode VMware credentials [IMPLEMENTED v1.0.0]
   - Use Kubernetes Secrets for credential storage [IMPLEMENTED v1.0.0]
   - Implement proper error handling for authentication failures [IMPLEMENTED v1.0.0]

## Prometheus Integration

When exposing metrics to Prometheus:

1. **Metric Types**:
   - Use appropriate metric types (Counter, Gauge, Histogram, Summary) [IMPLEMENTED v1.0.0]
   - Document metric types and units [IMPLEMENTED v1.0.0]
   - Follow Prometheus naming conventions [IMPLEMENTED v1.0.0]

2. **Labels**:
   - Use consistent labels across related metrics [IMPLEMENTED v1.0.0]
   - Avoid high cardinality labels [IMPLEMENTED v1.0.0]
   - Include labels that facilitate useful queries [IMPLEMENTED v1.0.0]

3. **Endpoint Configuration**:
   - Expose metrics on `/metrics` endpoint [IMPLEMENTED v1.0.0]
   - Make port configurable (default: 9090) [IMPLEMENTED v1.0.0]
   - Include appropriate Prometheus annotations in Kubernetes manifests [IMPLEMENTED v1.0.0]

## Testing

- Write unit tests for all code
- Use pytest for running tests
- Aim for high test coverage
- Write integration tests for critical functionality
- Write end-to-end tests for complete workflows
- Mock external dependencies (Kubernetes API, VMware API)

### Testing Monitoring Applications

For monitoring applications, include specific tests for:

1. **Metric Collection**:
   - Test metric collection with mock data [IMPLEMENTED v1.0.0]
   - Verify correct handling of edge cases [IMPLEMENTED v1.0.0]
   - Test rate limiting functionality [IMPLEMENTED v1.0.0]

2. **Alert Generation**:
   - Test alert thresholds [IMPLEMENTED v1.0.0]
   - Verify alert formatting [IMPLEMENTED v1.0.0]
   - Test alert deduplication [IMPLEMENTED v1.0.0]

3. **Prometheus Integration**:
   - Test metric exposition format [IMPLEMENTED v1.0.0]
   - Verify label consistency [IMPLEMENTED v1.0.0]
   - Test metric registration [IMPLEMENTED v1.0.0]

## Container Development

- Use Dockerfile for containerizing applications
- Base containers on one of the following:
  - CentOS Stream
  - Fedora Stream
  - Alpine
- Follow best practices for container security
- Minimize container size
- Use multi-stage builds when appropriate

## Kubernetes Development

- Follow the [Kubernetes API conventions](https://github.com/kubernetes/community/blob/master/contributors/devel/sig-architecture/api-conventions.md)
- Use namespaces to organize resources
- Use labels and annotations for resource organization
- Use ConfigMaps and Secrets for configuration
- Implement proper RBAC for security
- Use Kustomize for environment-specific configurations

### Kubernetes Deployment Manifests

For each application, create the following manifests:

1. **Deployment/StatefulSet**:
   - Include resource limits and requests
   - Configure liveness and readiness probes
   - Set appropriate update strategy

2. **Service**:
   - Expose necessary ports
   - Include appropriate annotations for Prometheus

3. **ConfigMap**:
   - Include all configurable parameters
   - Document each parameter with comments

4. **Secret**:
   - Store sensitive information
   - Reference in deployment using environment variables

5. **RBAC**:
   - Create ServiceAccount, Role/ClusterRole, and RoleBinding/ClusterRoleBinding
   - Follow principle of least privilege

6. **Kustomization**:
   - Configure resource variants for different environments
   - Include all resources in kustomization.yaml

## Documentation

- Document all code with docstrings
- Update README.md with relevant information
- Keep documentation up-to-date with code changes
- Document API endpoints with examples
- Document deployment procedures

### Application Documentation

For each application, document:

1. **Purpose and Features**:
   - What the application does
   - Key features and capabilities

2. **Configuration**:
   - Available configuration parameters
   - Environment variables
   - ConfigMap options

3. **Metrics**:
   - List of exposed metrics
   - Metric types and units
   - Label descriptions

4. **Deployment**:
   - Deployment prerequisites
   - Deployment steps
   - Verification procedures

## Security

- Never hardcode secrets in the codebase
- Use environment variables or Kubernetes Secrets for sensitive information
- Implement proper authentication and authorization
- Follow the principle of least privilege
- Regularly update dependencies to address security vulnerabilities
- Implement proper error handling to avoid information leakage
- Use HTTPS for all external communications
