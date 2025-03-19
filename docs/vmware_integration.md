# VMware Integration Guide

This document provides comprehensive information about the VMware integration features in the Kubernetes Playground project.

## Navigation

- [Main README](../README.md)
- [Documentation Index](index.md)
- [Setup Guide](setup.md)
- [Project Organization](project_organization.md)
- [Development Guidelines](development.md)
- [Deployment Guide](deployment.md)
- **VMware Integration Guide** (You are here)

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Configuration](#configuration)
  - [Required Credentials](#required-credentials)
  - [Connection Settings](#connection-settings)
  - [Monitoring Settings](#monitoring-settings)
- [Node-to-VM Correlation](#node-to-vm-correlation)
- [Targeted Monitoring](#targeted-monitoring)
- [Monitoring Triggers](#monitoring-triggers)
- [Metrics](#metrics)
- [Troubleshooting](#troubleshooting)

## Last Updated

March 19, 2025

## Overview

The VMware integration in the Kubernetes Playground project enables monitoring applications to check the status of the VMware infrastructure that hosts Kubernetes nodes. This is particularly valuable for troubleshooting when pods aren't running properly, as it provides correlation between Kubernetes issues and potential underlying VMware infrastructure problems.

## Key Features

- **VM Power State Monitoring**: Checks if VMware guests that Kubernetes nodes are running on are operational
- **ESXi Host Status Checking**: Verifies if ESXi hosts running the guests have any errors or alerts
- **Datastore Capacity Monitoring**: Monitors datastores assigned to VMs for events, alerts, and capacity issues
- **VM-to-Node Correlation**: Establishes reliable mapping between Kubernetes nodes and VMware VMs

## Architecture

The VMware integration is implemented as part of the Pod Monitor application. When a pod is not running properly or a VM is in a problematic state, the Pod Monitor will:

1. Identify the Kubernetes node hosting the pod
2. Correlate the node with its corresponding VMware VM
3. Check the VM's power state and configuration
4. Examine the ESXi host running the VM
5. Monitor datastores assigned to the VM
6. Expose relevant metrics to Prometheus
7. Log alerts for any detected issues

This focused approach ensures that VMware monitoring is performed specifically when troubleshooting is needed, providing valuable correlation between pod failures and potential infrastructure issues.

## Configuration

### Required Credentials

VMware integration requires credentials for accessing the vCenter Server or ESXi host. These should be stored in a Kubernetes Secret:

```bash
kubectl create secret generic pod-monitor-vmware-credentials \
  --from-literal=host=vcenter.example.com \
  --from-literal=username=your-vmware-username \
  --from-literal=password=your-vmware-password \
  -n monitoring
```

### Connection Settings

The following connection settings can be configured through the Pod Monitor ConfigMap:

| Option | Description | Default | Status |
|--------|-------------|---------|--------|
| `vmware.host` | VMware vCenter/ESXi host | Required | [IMPLEMENTED v1.0.0] |
| `vmware.username` | VMware username | Required | [IMPLEMENTED v1.0.0] |
| `vmware.password` | VMware password | Required | [IMPLEMENTED v1.0.0] |
| `vmware.port` | VMware API port | `443` | [IMPLEMENTED v1.0.0] |
| `vmware.disable_ssl_verification` | Whether to disable SSL verification | `false` | [IMPLEMENTED v1.0.0] |

### Monitoring Settings

The following monitoring settings can be configured:

| Option | Description | Default | Status |
|--------|-------------|---------|--------|
| `vmware.datastore.low_space_threshold` | Percentage threshold for datastore low space alerts | `10` | [IMPLEMENTED v1.0.0] |
| `vmware.check_interval` | Interval in seconds between VMware checks | `300` | [IMPLEMENTED v1.0.0] |
| `pod_label_selectors` | Labels to filter which pods to monitor | `{}` | [IMPLEMENTED v1.0.0] |
| `monitor_all_nodes` | Whether to monitor all nodes or only those running selected pods | `false` | [IMPLEMENTED v1.0.0] |

## Node-to-VM Correlation

The Pod Monitor correlates Kubernetes nodes with VMware VMs using the following methods:

1. **VM Name Label**: Kubernetes nodes can be labeled with their corresponding VMware VM names:

   ```bash
   kubectl label node worker-1 vm-name=worker-1-vm
   ```

2. **Node Name Matching**: If the `vm-name` label is not present, the system will use the node name as the VMware guest name.

This correlation is critical for properly monitoring the VMware infrastructure associated with specific Kubernetes nodes.

## Targeted Monitoring

To optimize vCenter performance in large clusters, the Pod Monitor supports targeted monitoring:

1. **Pod Label Selectors**: Only monitor pods (and their nodes) that match specific labels
   - Configure with comma-separated key=value pairs (e.g., `app=critical,tier=production`)
   - This significantly reduces the number of VMware API calls in large clusters

2. **Selective Node Monitoring**: By default, only nodes running the selected pods will be monitored
   - This prevents unnecessary VMware API calls for nodes not running critical workloads
   - Set `monitor_all_nodes: "true"` to monitor all nodes regardless of pod selection

This targeted approach is especially beneficial in large clusters with hundreds of nodes, as it minimizes the impact on your vCenter Server while still providing critical monitoring for your most important workloads.

## Monitoring Triggers

VMware infrastructure checks are triggered when:

- A pod is not running properly (status is not "Running")
- A node is not in "Ready" state
- A VM is in a problematic state (powered off, suspended, etc.)
- The regular monitoring interval is reached

## Metrics

The Pod Monitor exposes the following VMware-related metrics to Prometheus:

| Metric Name | Type | Description | Labels |
|-------------|------|-------------|--------|
| `vmware_vm_power_state` | Gauge | Power state of the VM (1=on, 0=off) | `vm_name`, `node_name` |
| `vmware_esxi_host_status` | Gauge | Status of the ESXi host (1=ok, 0=error) | `host_name`, `node_name` |
| `vmware_datastore_capacity_bytes` | Gauge | Total capacity of the datastore in bytes | `datastore_name` |
| `vmware_datastore_free_bytes` | Gauge | Free space on the datastore in bytes | `datastore_name` |
| `vmware_datastore_usage_percent` | Gauge | Percentage of datastore space used | `datastore_name` |

## Troubleshooting

Common issues with VMware integration:

1. **Connection Failures**:
   - Verify network connectivity from the Kubernetes cluster to the VMware environment
   - Check that the provided credentials are correct
   - Ensure the user account has sufficient permissions

2. **VM Correlation Issues**:
   - Verify that node names match VM names in vCenter
   - Check that `vm-name` labels are correctly applied to nodes
   - Look for correlation errors in the Pod Monitor logs

3. **Missing Metrics**:
   - Verify that the Pod Monitor is correctly configured for VMware integration
   - Check that the VMware credentials secret is properly created
   - Look for VMware-related errors in the Pod Monitor logs

For detailed troubleshooting, check the Pod Monitor logs:

```bash
kubectl logs -f deployment/pod-monitor -n monitoring | grep VMware
```
