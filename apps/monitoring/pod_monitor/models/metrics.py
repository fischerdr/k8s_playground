"""Metrics models for pod monitoring.

This module defines data models for Kubernetes pod, node, and VMware machine metrics.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


class PodStatus(str, Enum):
    """Enum representing Kubernetes pod statuses."""

    RUNNING = "Running"
    PENDING = "Pending"
    SUCCEEDED = "Succeeded"
    FAILED = "Failed"
    UNKNOWN = "Unknown"
    CRASH_LOOP_BACKOFF = "CrashLoopBackOff"

    @classmethod
    def is_problematic(cls, status: str) -> bool:
        """Check if the pod status is problematic.

        Args:
            status: Pod status string

        Returns:
            True if the status is problematic, False otherwise
        """
        problematic_statuses = [
            cls.PENDING.value,
            cls.FAILED.value,
            cls.UNKNOWN.value,
            cls.CRASH_LOOP_BACKOFF.value,
        ]
        return status in problematic_statuses


class NodeStatus(str, Enum):
    """Enum representing Kubernetes node statuses."""

    READY = "Ready"
    NOT_READY = "NotReady"
    UNKNOWN = "Unknown"

    @classmethod
    def is_problematic(cls, status: str) -> bool:
        """Check if the node status is problematic.

        Args:
            status: Node status string

        Returns:
            True if the status is problematic, False otherwise
        """
        return status != cls.READY.value


class VMwareStatus(str, Enum):
    """Enum representing VMware machine statuses."""

    POWERED_ON = "poweredOn"
    POWERED_OFF = "poweredOff"
    SUSPENDED = "suspended"
    DISCONNECTED = "disconnected"

    @classmethod
    def is_problematic(cls, status: str) -> bool:
        """Check if the VMware status is problematic.

        Args:
            status: VMware status string

        Returns:
            True if the status is problematic, False otherwise
        """
        problematic_statuses = [
            cls.POWERED_OFF.value,
            cls.SUSPENDED.value,
            cls.DISCONNECTED.value,
        ]
        return status in problematic_statuses


@dataclass
class PodMetric:
    """Metric for a Kubernetes pod."""

    name: str
    namespace: str
    status: str
    node_name: Optional[str] = None
    start_time: Optional[datetime] = None
    containers: List[str] = field(default_factory=list)
    container_statuses: Dict[str, str] = field(default_factory=dict)
    labels: Dict[str, str] = field(default_factory=dict)

    @property
    def age(self) -> Optional[float]:
        """Calculate pod age in seconds."""
        if self.start_time:
            return (datetime.now() - self.start_time).total_seconds()
        return None

    @property
    def is_problematic(self) -> bool:
        """Check if the pod status is problematic."""
        return PodStatus.is_problematic(self.status)

    def to_prometheus(self) -> List[str]:
        """Convert to Prometheus metrics format."""
        metrics = []

        # Basic status metric (0 = problematic, 1 = ok)
        status_value = 0 if self.is_problematic else 1
        labels = f'namespace="{self.namespace}",pod="{self.name}",status="{self.status}"'
        if self.node_name:
            labels += f',node="{self.node_name}"'

        metrics.append(f"k8s_pod_status{{{labels}}} {status_value}")

        # Add container status metrics if available
        for container, status in self.container_statuses.items():
            container_status_value = 0 if status != "running" else 1
            container_labels = f'namespace="{self.namespace}",pod="{self.name}",container="{container}",status="{status}"'
            metrics.append(f"k8s_container_status{{{container_labels}}} {container_status_value}")

        # Add pod age metric if available
        if self.age is not None:
            metrics.append(f"k8s_pod_age_seconds{{{labels}}} {self.age}")

        return metrics


@dataclass
class NodeMetric:
    """Metric for a Kubernetes node."""

    name: str
    status: str
    vmware_machine_name: Optional[str] = None
    conditions: Dict[str, bool] = field(default_factory=dict)
    labels: Dict[str, str] = field(default_factory=dict)

    @property
    def is_problematic(self) -> bool:
        """Check if the node status is problematic."""
        return NodeStatus.is_problematic(self.status)

    def to_prometheus(self) -> List[str]:
        """Convert to Prometheus metrics format."""
        metrics = []

        # Basic status metric (0 = problematic, 1 = ok)
        status_value = 0 if self.is_problematic else 1
        labels = f'node="{self.name}",status="{self.status}"'
        if self.vmware_machine_name:
            labels += f',vmware_machine="{self.vmware_machine_name}"'

        metrics.append(f"k8s_node_status{{{labels}}} {status_value}")

        # Add condition metrics
        for condition, value in self.conditions.items():
            condition_value = 1 if value else 0
            condition_labels = f'node="{self.name}",condition="{condition}"'
            metrics.append(f"k8s_node_condition{{{condition_labels}}} {condition_value}")

        return metrics


@dataclass
class VMwareMetric:
    """Metric for a VMware machine."""

    name: str
    status: str
    node_name: str
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None
    cpu_capacity: Optional[float] = None
    memory_capacity: Optional[float] = None

    @property
    def is_problematic(self) -> bool:
        """Check if the VMware status is problematic."""
        return VMwareStatus.is_problematic(self.status)

    @property
    def cpu_percent(self) -> Optional[float]:
        """Calculate CPU usage percentage."""
        if self.cpu_usage is not None and self.cpu_capacity is not None and self.cpu_capacity > 0:
            return (self.cpu_usage / self.cpu_capacity) * 100
        return None

    @property
    def memory_percent(self) -> Optional[float]:
        """Calculate memory usage percentage."""
        if (
            self.memory_usage is not None
            and self.memory_capacity is not None
            and self.memory_capacity > 0
        ):
            return (self.memory_usage / self.memory_capacity) * 100
        return None

    def to_prometheus(self) -> List[str]:
        """Convert to Prometheus metrics format."""
        metrics = []

        # Basic status metric (0 = problematic, 1 = ok)
        status_value = 0 if self.is_problematic else 1
        labels = f'vmware_machine="{self.name}",status="{self.status}",node="{self.node_name}"'

        metrics.append(f"vmware_machine_status{{{labels}}} {status_value}")

        # Add resource metrics if available
        if self.cpu_usage is not None:
            metrics.append(f"vmware_machine_cpu_usage{{{labels}}} {self.cpu_usage}")

        if self.memory_usage is not None:
            metrics.append(f"vmware_machine_memory_usage{{{labels}}} {self.memory_usage}")

        if self.cpu_percent is not None:
            metrics.append(f"vmware_machine_cpu_percent{{{labels}}} {self.cpu_percent}")

        if self.memory_percent is not None:
            metrics.append(f"vmware_machine_memory_percent{{{labels}}} {self.memory_percent}")

        return metrics
