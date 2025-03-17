"""Cluster metrics models.

This module defines data models for Kubernetes cluster metrics.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class NodeMetrics:
    """Metrics for a Kubernetes node."""

    name: str
    cpu_usage: float
    memory_usage: float
    cpu_capacity: float
    memory_capacity: float
    pods_running: int
    conditions: Dict[str, bool] = field(default_factory=dict)

    @property
    def cpu_percent(self) -> float:
        """Calculate CPU usage percentage."""
        return (self.cpu_usage / self.cpu_capacity) * 100 if self.cpu_capacity else 0

    @property
    def memory_percent(self) -> float:
        """Calculate memory usage percentage."""
        return (self.memory_usage / self.memory_capacity) * 100 if self.memory_capacity else 0

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "cpu_usage": self.cpu_usage,
            "memory_usage": self.memory_usage,
            "cpu_capacity": self.cpu_capacity,
            "memory_capacity": self.memory_capacity,
            "cpu_percent": self.cpu_percent,
            "memory_percent": self.memory_percent,
            "pods_running": self.pods_running,
            "conditions": self.conditions,
        }

    def to_prometheus(self) -> List[str]:
        """Convert to Prometheus metrics format."""
        metrics = []
        metrics.append(f'node_cpu_usage{{node="{self.name}"}} {self.cpu_usage}')
        metrics.append(f'node_memory_usage{{node="{self.name}"}} {self.memory_usage}')
        metrics.append(f'node_cpu_percent{{node="{self.name}"}} {self.cpu_percent}')
        metrics.append(f'node_memory_percent{{node="{self.name}"}} {self.memory_percent}')
        metrics.append(f'node_pods_running{{node="{self.name}"}} {self.pods_running}')

        for condition, status in self.conditions.items():
            metrics.append(
                f'node_condition{{node="{self.name}",condition="{condition}"}} {1 if status else 0}'
            )

        return metrics


@dataclass
class ClusterMetrics:
    """Metrics for a Kubernetes cluster."""

    nodes: List[NodeMetrics] = field(default_factory=list)
    total_nodes: int = 0
    healthy_nodes: int = 0
    total_pods: int = 0
    namespace: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "total_nodes": self.total_nodes,
            "healthy_nodes": self.healthy_nodes,
            "total_pods": self.total_pods,
            "namespace": self.namespace,
            "nodes": [node.to_dict() for node in self.nodes],
        }

    def to_prometheus(self) -> List[str]:
        """Convert to Prometheus metrics format."""
        metrics = []
        namespace_label = f',namespace="{self.namespace}"' if self.namespace else ""

        metrics.append(f"cluster_total_nodes{namespace_label} {self.total_nodes}")
        metrics.append(f"cluster_healthy_nodes{namespace_label} {self.healthy_nodes}")
        metrics.append(f"cluster_total_pods{namespace_label} {self.total_pods}")

        for node in self.nodes:
            metrics.extend(node.to_prometheus())

        return metrics
