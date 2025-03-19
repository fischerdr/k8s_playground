# Setup Guide

This document provides instructions for setting up the Kubernetes Playground project.

## Navigation

- [Main README](../README.md)
- [Documentation Index](index.md)
- **Setup Guide** (You are here)
- [Project Organization](project_organization.md)
- [Development Guidelines](development.md)
- [Deployment Guide](deployment.md)
- [VMware Integration Guide](vmware_integration.md)

## Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Setup](#environment-setup)
  - [Python Environment](#python-environment)
  - [Kubernetes Setup](#kubernetes-setup)
- [Docker/Podman Setup](#dockerpodman-setup)
- [Development Environment Configuration](#development-environment-configuration)
- [Next Steps](#next-steps)

## Last Updated

March 19, 2025

## Prerequisites

- Python 3.9 or higher (up to 3.14)
- Docker or Podman
- Access to a Kubernetes cluster (local or remote)
- Git

## Environment Setup

### Python Environment

1. Clone the repository:

   ```bash
   git clone https://github.com/example/k8s_playground.git
   cd k8s_playground
   ```

2. Create a virtual environment:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # For development
   ```

### Kubernetes Setup

1. Ensure you have access to a Kubernetes cluster:
   - For local development, [minikube](https://minikube.sigs.k8s.io/docs/start/) is recommended
   - For production, ensure you have proper credentials for your target cluster

2. Verify your Kubernetes connection:

   ```bash
   kubectl cluster-info
   kubectl get nodes
   ```

3. Create the necessary namespaces:

   ```bash
   kubectl create namespace monitoring
   ```

## Docker/Podman Setup

1. Ensure Docker or Podman is installed and running:

   ```bash
   # For Docker
   docker --version
   
   # For Podman
   podman --version
   ```

2. Configure Docker/Podman to use the appropriate base images:
   - CentOS Stream
   - Fedora Stream
   - Alpine

## Development Environment Configuration

1. Configure your IDE with the following settings:
   - Python interpreter: `.venv/bin/python`
   - Linting: flake8, black, isort
   - Line length: 88 characters (Black default)

2. Set up pre-commit hooks (optional):

   ```bash
   pip install pre-commit
   pre-commit install
   ```

## Next Steps

After completing the setup process:

1. Review the [Project Organization](project_organization.md) document to understand the project structure
2. Follow the [Development Guidelines](development.md) for coding standards and practices
3. Use the [Deployment Guide](deployment.md) for instructions on deploying the applications

For VMware integration setup, refer to the [VMware Integration Guide](vmware_integration.md).
