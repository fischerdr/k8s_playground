"""Prometheus integration service.

This module provides services for exposing metrics to Prometheus.
"""

import logging
import threading
import time
from typing import Callable, Dict, List, Optional

from prometheus_client import Counter, Gauge, start_http_server

from ..models.metrics import NodeMetric, PodMetric, VMwareMetric

log = logging.getLogger("pod_monitor")


class PrometheusService:
    """Service for exposing metrics to Prometheus."""

    def __init__(self, port: int = 9090) -> None:
        """Initialize the Prometheus service.

        Args:
            port: Port to expose metrics on
        """
        self.port = port
        self.server_started = False
        self.server_thread = None

        # Create metrics
        self.pod_status_gauge = Gauge(
            "k8s_pod_status",
            "Status of Kubernetes pods (0=problematic, 1=ok)",
            ["namespace", "pod", "status", "node"],
        )

        self.pod_age_gauge = Gauge(
            "k8s_pod_age_seconds",
            "Age of Kubernetes pods in seconds",
            ["namespace", "pod", "status", "node"],
        )

        self.container_status_gauge = Gauge(
            "k8s_container_status",
            "Status of Kubernetes containers (0=problematic, 1=ok)",
            ["namespace", "pod", "container", "status"],
        )

        self.node_status_gauge = Gauge(
            "k8s_node_status",
            "Status of Kubernetes nodes (0=problematic, 1=ok)",
            ["node", "status", "vmware_machine"],
        )

        self.node_condition_gauge = Gauge(
            "k8s_node_condition",
            "Conditions of Kubernetes nodes (0=false, 1=true)",
            ["node", "condition"],
        )

        self.vmware_status_gauge = Gauge(
            "vmware_machine_status",
            "Status of VMware machines (0=problematic, 1=ok)",
            ["vmware_machine", "status", "node"],
        )

        self.vmware_cpu_usage_gauge = Gauge(
            "vmware_machine_cpu_usage",
            "CPU usage of VMware machines in MHz",
            ["vmware_machine", "node"],
        )

        self.vmware_memory_usage_gauge = Gauge(
            "vmware_machine_memory_usage",
            "Memory usage of VMware machines in bytes",
            ["vmware_machine", "node"],
        )

        self.vmware_cpu_percent_gauge = Gauge(
            "vmware_machine_cpu_percent",
            "CPU usage percentage of VMware machines",
            ["vmware_machine", "node"],
        )

        self.vmware_memory_percent_gauge = Gauge(
            "vmware_machine_memory_percent",
            "Memory usage percentage of VMware machines",
            ["vmware_machine", "node"],
        )

        self.alert_counter = Counter(
            "k8s_monitor_alerts_total",
            "Total number of alerts generated",
            ["alert_type", "resource_type"],
        )

    def start_server(self) -> None:
        """Start the Prometheus metrics server."""
        if not self.server_started:
            log.info(f"Starting Prometheus metrics server on port {self.port}")

            def server_thread_func():
                start_http_server(self.port)
                log.info(f"Prometheus metrics server started on port {self.port}")

                # Keep thread alive
                while True:
                    time.sleep(60)

            self.server_thread = threading.Thread(
                target=server_thread_func,
                daemon=True,
            )
            self.server_thread.start()

            self.server_started = True
        else:
            log.warning("Prometheus metrics server already started")

    def update_pod_metrics(self, pod_metrics: List[PodMetric]) -> None:
        """Update Prometheus metrics for pods.

        Args:
            pod_metrics: List of PodMetric objects
        """
        # Clear existing pod metrics
        self.pod_status_gauge._metrics.clear()
        self.pod_age_gauge._metrics.clear()
        self.container_status_gauge._metrics.clear()

        for pod in pod_metrics:
            # Update pod status metric
            status_value = 0 if pod.is_problematic else 1
            self.pod_status_gauge.labels(
                namespace=pod.namespace,
                pod=pod.name,
                status=pod.status,
                node=pod.node_name or "unknown",
            ).set(status_value)

            # Update pod age metric if available
            if pod.age is not None:
                self.pod_age_gauge.labels(
                    namespace=pod.namespace,
                    pod=pod.name,
                    status=pod.status,
                    node=pod.node_name or "unknown",
                ).set(pod.age)

            # Update container status metrics
            for container, status in pod.container_statuses.items():
                container_status_value = 0 if status != "running" else 1
                self.container_status_gauge.labels(
                    namespace=pod.namespace,
                    pod=pod.name,
                    container=container,
                    status=status,
                ).set(container_status_value)

    def update_node_metrics(self, node_metrics: List[NodeMetric]) -> None:
        """Update Prometheus metrics for nodes.

        Args:
            node_metrics: List of NodeMetric objects
        """
        # Clear existing node metrics
        self.node_status_gauge._metrics.clear()
        self.node_condition_gauge._metrics.clear()

        for node in node_metrics:
            # Update node status metric
            status_value = 0 if node.is_problematic else 1
            self.node_status_gauge.labels(
                node=node.name,
                status=node.status,
                vmware_machine=node.vmware_machine_name or "unknown",
            ).set(status_value)

            # Update node condition metrics
            for condition, value in node.conditions.items():
                condition_value = 1 if value else 0
                self.node_condition_gauge.labels(
                    node=node.name,
                    condition=condition,
                ).set(condition_value)

    def update_vmware_metrics(self, vmware_metrics: List[VMwareMetric]) -> None:
        """Update Prometheus metrics for VMware machines.

        Args:
            vmware_metrics: List of VMwareMetric objects
        """
        # Clear existing VMware metrics
        self.vmware_status_gauge._metrics.clear()
        self.vmware_cpu_usage_gauge._metrics.clear()
        self.vmware_memory_usage_gauge._metrics.clear()
        self.vmware_cpu_percent_gauge._metrics.clear()
        self.vmware_memory_percent_gauge._metrics.clear()

        for vm in vmware_metrics:
            # Update VM status metric
            status_value = 0 if vm.is_problematic else 1
            self.vmware_status_gauge.labels(
                vmware_machine=vm.name,
                status=vm.status,
                node=vm.node_name,
            ).set(status_value)

            # Update VM resource metrics if available
            if vm.cpu_usage is not None:
                self.vmware_cpu_usage_gauge.labels(
                    vmware_machine=vm.name,
                    node=vm.node_name,
                ).set(vm.cpu_usage)

            if vm.memory_usage is not None:
                self.vmware_memory_usage_gauge.labels(
                    vmware_machine=vm.name,
                    node=vm.node_name,
                ).set(vm.memory_usage)

            if vm.cpu_percent is not None:
                self.vmware_cpu_percent_gauge.labels(
                    vmware_machine=vm.name,
                    node=vm.node_name,
                ).set(vm.cpu_percent)

            if vm.memory_percent is not None:
                self.vmware_memory_percent_gauge.labels(
                    vmware_machine=vm.name,
                    node=vm.node_name,
                ).set(vm.memory_percent)

    def record_alert(self, alert_type: str, resource_type: str) -> None:
        """Record an alert in Prometheus metrics.

        Args:
            alert_type: Type of alert (e.g., "status", "resource")
            resource_type: Type of resource (e.g., "pod", "node", "vmware")
        """
        self.alert_counter.labels(
            alert_type=alert_type,
            resource_type=resource_type,
        ).inc()
