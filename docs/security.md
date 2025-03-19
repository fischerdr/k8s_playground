# Security Guide

This document provides comprehensive security guidelines and best practices for the Kubernetes Playground project.

## Navigation

- [Main README](../README.md)
- [Documentation Index](index.md)
- [Setup Guide](setup.md)
- [Project Organization](project_organization.md)
- [Development Guidelines](development.md)
- [Deployment Guide](deployment.md)
- [VMware Integration Guide](vmware_integration.md)
- **Security Guide** (You are here)

## Table of Contents

- [Overview](#overview)
- [RBAC Configuration](#rbac-configuration)
  - [Pod Monitor RBAC](#pod-monitor-rbac)
  - [Cluster Monitor RBAC](#cluster-monitor-rbac)
  - [Custom RBAC Examples](#custom-rbac-examples)
- [Network Policies](#network-policies)
  - [Default Deny Policy](#default-deny-policy)
  - [Pod Monitor Network Policy](#pod-monitor-network-policy)
  - [Cluster Monitor Network Policy](#cluster-monitor-network-policy)
- [Pod Security](#pod-security)
  - [Security Context](#security-context)
  - [Pod Security Standards](#pod-security-standards)
- [Secrets Management](#secrets-management)
  - [Kubernetes Secrets](#kubernetes-secrets)
  - [VMware Credentials](#vmware-credentials)
  - [External Secret Stores](#external-secret-stores)
- [Container Security](#container-security)
  - [Base Image Selection](#base-image-selection)
  - [Image Scanning](#image-scanning)
  - [Runtime Security](#runtime-security)
- [Audit Logging](#audit-logging)
- [Security Checklist](#security-checklist)

## Last Updated

March 19, 2025

## Overview

Security is a critical aspect of any Kubernetes deployment. This guide provides comprehensive security recommendations for the Kubernetes Playground project, focusing on RBAC, network policies, pod security, and secrets management.

## RBAC Configuration

Role-Based Access Control (RBAC) is essential for limiting access to Kubernetes resources. The following sections provide detailed RBAC configurations for different components.

### Pod Monitor RBAC

The Pod Monitor requires specific permissions to monitor pods and nodes:

```yaml
# Pod Monitor RBAC Configuration
apiVersion: v1
kind: ServiceAccount
metadata:
  name: pod-monitor
  namespace: monitoring
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: pod-monitor
rules:
- apiGroups: [""]
  resources: ["pods", "nodes"]
  verbs: ["get", "list", "watch"]
- apiGroups: [""]
  resources: ["namespaces"]
  verbs: ["get", "list"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: pod-monitor
subjects:
- kind: ServiceAccount
  name: pod-monitor
  namespace: monitoring
roleRef:
  kind: ClusterRole
  name: pod-monitor
  apiGroup: rbac.authorization.k8s.io
```

### Cluster Monitor RBAC

The Cluster Monitor requires broader permissions to monitor cluster-wide resources:

```yaml
# Cluster Monitor RBAC Configuration
apiVersion: v1
kind: ServiceAccount
metadata:
  name: cluster-monitor
  namespace: monitoring
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: cluster-monitor
rules:
- apiGroups: [""]
  resources: ["nodes", "namespaces", "pods", "services", "endpoints"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments", "daemonsets", "statefulsets"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["batch"]
  resources: ["jobs", "cronjobs"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: cluster-monitor
subjects:
- kind: ServiceAccount
  name: cluster-monitor
  namespace: monitoring
roleRef:
  kind: ClusterRole
  name: cluster-monitor
  apiGroup: rbac.authorization.k8s.io
```

### Custom RBAC Examples

#### Namespace-Restricted Monitoring

For environments where you want to restrict monitoring to specific namespaces:

```yaml
# Namespace-Restricted RBAC
apiVersion: v1
kind: ServiceAccount
metadata:
  name: namespace-restricted-monitor
  namespace: monitoring
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: pod-monitor
  namespace: app-namespace-1
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: pod-monitor
  namespace: app-namespace-1
subjects:
- kind: ServiceAccount
  name: namespace-restricted-monitor
  namespace: monitoring
roleRef:
  kind: Role
  name: pod-monitor
  apiGroup: rbac.authorization.k8s.io
```

Repeat the Role and RoleBinding for each namespace you want to monitor.

#### Read-Only Admin

For users who need to view but not modify resources:

```yaml
# Read-Only Admin RBAC
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: read-only-admin
rules:
- apiGroups: ["*"]
  resources: ["*"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: read-only-admin
subjects:
- kind: User
  name: read-only-user
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole
  name: read-only-admin
  apiGroup: rbac.authorization.k8s.io
```

## Network Policies

Network Policies control the traffic flow between pods and external services. Implementing proper network policies is crucial for securing your Kubernetes environment.

### Default Deny Policy

Start with a default deny policy to block all ingress and egress traffic, then add specific allowances:

```yaml
# Default Deny Policy
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny
  namespace: monitoring
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
```

### Pod Monitor Network Policy

Allow specific traffic to and from the Pod Monitor:

```yaml
# Pod Monitor Network Policy
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: pod-monitor-network-policy
  namespace: monitoring
spec:
  podSelector:
    matchLabels:
      app: pod-monitor
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          kubernetes.io/metadata.name: monitoring
    ports:
    - protocol: TCP
      port: 9090  # Prometheus metrics port
    - protocol: TCP
      port: 8080  # API port
  egress:
  - to:
    - ipBlock:
        cidr: 0.0.0.0/0
        except:
        - 169.254.0.0/16
        - 172.16.0.0/12
    ports:
    - protocol: TCP
      port: 443  # For Kubernetes API and VMware API
    - protocol: TCP
      port: 6443  # For Kubernetes API
```

### Cluster Monitor Network Policy

Similar policy for the Cluster Monitor:

```yaml
# Cluster Monitor Network Policy
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: cluster-monitor-network-policy
  namespace: monitoring
spec:
  podSelector:
    matchLabels:
      app: cluster-monitor
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          kubernetes.io/metadata.name: monitoring
    ports:
    - protocol: TCP
      port: 9091  # Prometheus metrics port
    - protocol: TCP
      port: 8080  # API port
  egress:
  - to:
    - ipBlock:
        cidr: 0.0.0.0/0
        except:
        - 169.254.0.0/16
        - 172.16.0.0/12
    ports:
    - protocol: TCP
      port: 443  # For Kubernetes API
    - protocol: TCP
      port: 6443  # For Kubernetes API
```

## Pod Security

### Security Context

Always define security contexts for your pods to enforce least privilege:

```yaml
# Pod Security Context Example
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  runAsGroup: 3000
  fsGroup: 2000
  allowPrivilegeEscalation: false
  capabilities:
    drop:
    - ALL
  seccompProfile:
    type: RuntimeDefault
```

### Pod Security Standards

Kubernetes defines three Pod Security Standards:

1. **Privileged**: Unrestricted policy, providing the widest possible level of permissions
2. **Baseline**: Minimally restrictive policy which prevents known privilege escalations
3. **Restricted**: Heavily restricted policy, following current pod hardening best practices

For the Kubernetes Playground, we recommend using the **Restricted** policy where possible, or at minimum the **Baseline** policy:

```yaml
# Pod Security Standard Label
apiVersion: v1
kind: Namespace
metadata:
  name: monitoring
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

## Secrets Management

### Kubernetes Secrets

While Kubernetes Secrets are convenient, they are only base64 encoded by default. Consider these best practices:

1. Enable encryption at rest for etcd:

```yaml
# Example etcd encryption configuration
apiVersion: apiserver.config.k8s.io/v1
kind: EncryptionConfiguration
resources:
  - resources:
    - secrets
    providers:
    - aescbc:
        keys:
        - name: key1
          secret: <base64-encoded-key>
    - identity: {}
```

2. Limit access to Secrets with RBAC:

```yaml
# Restrict Secret Access
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: monitoring
  name: secret-reader
rules:
- apiGroups: [""]
  resources: ["secrets"]
  verbs: ["get", "list"]
  resourceNames: ["pod-monitor-vmware-credentials"]
```

### VMware Credentials

For VMware credentials, follow these security practices:

1. Create a dedicated service account in VMware with minimal permissions
2. Store credentials in Kubernetes Secrets:

```yaml
# VMware Credentials Secret
apiVersion: v1
kind: Secret
metadata:
  name: vmware-credentials
  namespace: monitoring
type: Opaque
data:
  host: <base64-encoded-host>
  username: <base64-encoded-username>
  password: <base64-encoded-password>
```

3. Mount the secret as environment variables or files:

```yaml
# Mount as environment variables
env:
- name: VMWARE_HOST
  valueFrom:
    secretKeyRef:
      name: vmware-credentials
      key: host
- name: VMWARE_USERNAME
  valueFrom:
    secretKeyRef:
      name: vmware-credentials
      key: username
- name: VMWARE_PASSWORD
  valueFrom:
    secretKeyRef:
      name: vmware-credentials
      key: password

# Or mount as files
volumeMounts:
- name: vmware-credentials
  mountPath: "/etc/vmware"
  readOnly: true
volumes:
- name: vmware-credentials
  secret:
    secretName: vmware-credentials
```

### External Secret Stores

For production environments, consider using external secret management solutions:

1. **HashiCorp Vault**: Provides advanced secret management with dynamic secrets
2. **AWS Secrets Manager**: Managed service for storing and retrieving secrets
3. **Azure Key Vault**: Secure storage for keys, secrets, and certificates
4. **External Secrets Operator**: Kubernetes operator that integrates with external secret management systems

Example using External Secrets Operator with Vault:

```yaml
# External Secrets Operator with Vault
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: vmware-credentials
  namespace: monitoring
spec:
  refreshInterval: "15m"
  secretStoreRef:
    name: vault-backend
    kind: ClusterSecretStore
  target:
    name: vmware-credentials
  data:
  - secretKey: host
    remoteRef:
      key: kubernetes-playground/vmware
      property: host
  - secretKey: username
    remoteRef:
      key: kubernetes-playground/vmware
      property: username
  - secretKey: password
    remoteRef:
      key: kubernetes-playground/vmware
      property: password
```

## Container Security

### Base Image Selection

Choose secure base images for your containers:

1. Use minimal images like Alpine, Fedora Stream, or CentOS Stream
2. Regularly update base images to include security patches
3. Consider distroless images for production

### Image Scanning

Implement image scanning in your CI/CD pipeline:

1. Use tools like Trivy, Clair, or Snyk to scan for vulnerabilities
2. Enforce policies to prevent deployment of images with critical vulnerabilities
3. Regularly scan running containers

Example Trivy scan in CI:

```bash
# Scan container image with Trivy
trivy image k8s-playground/pod-monitor:latest --severity HIGH,CRITICAL
```

### Runtime Security

Implement runtime security measures:

1. Use admission controllers like OPA Gatekeeper or Kyverno to enforce policies
2. Consider runtime security tools like Falco for threat detection
3. Implement pod security policies (or Pod Security Standards in newer Kubernetes versions)

Example OPA Gatekeeper policy to require non-root containers:

```yaml
# OPA Gatekeeper policy for non-root containers
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sNonRootContainer
metadata:
  name: require-non-root-containers
spec:
  match:
    kinds:
      - apiGroups: [""]
        kinds: ["Pod"]
    namespaces:
      - "monitoring"
```

## Audit Logging

Enable audit logging in your Kubernetes cluster:

1. Configure the Kubernetes API server with audit logging:

```yaml
# Kubernetes API server audit configuration
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
- level: Metadata
  resources:
  - group: ""
    resources: ["secrets"]
- level: RequestResponse
  resources:
  - group: ""
    resources: ["pods"]
- level: Request
  resources:
  - group: ""
    resources: ["configmaps"]
- level: Metadata
  omitStages:
  - "RequestReceived"
```

2. Forward audit logs to a SIEM system for analysis
3. Set up alerts for suspicious activities

## Security Checklist

Use this checklist to ensure your Kubernetes Playground deployment is secure:

- [ ] **RBAC**
  - [ ] Use dedicated service accounts for each component
  - [ ] Apply the principle of least privilege
  - [ ] Regularly audit RBAC permissions

- [ ] **Network Security**
  - [ ] Implement default deny network policies
  - [ ] Define specific ingress and egress rules
  - [ ] Secure communication with TLS

- [ ] **Pod Security**
  - [ ] Set appropriate security contexts
  - [ ] Apply Pod Security Standards
  - [ ] Disable privileged containers

- [ ] **Secrets Management**
  - [ ] Encrypt Secrets at rest
  - [ ] Use external secret stores for production
  - [ ] Rotate credentials regularly

- [ ] **Container Security**
  - [ ] Use minimal, up-to-date base images
  - [ ] Scan images for vulnerabilities
  - [ ] Implement runtime security controls

- [ ] **Monitoring and Auditing**
  - [ ] Enable audit logging
  - [ ] Monitor for security events
  - [ ] Regularly review security posture

- [ ] **VMware Integration**
  - [ ] Use dedicated service accounts with minimal permissions
  - [ ] Secure API communication with TLS
  - [ ] Regularly rotate VMware credentials
