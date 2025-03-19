"""Kubernetes monitoring service.

This module provides services for monitoring Kubernetes pods and nodes.
"""

import logging
from typing import List, Optional, Tuple

from kubernetes import client, config, watch
from kubernetes.client.exceptions import ApiException

from ..models.metrics import NodeMetric, PodMetric

log = logging.getLogger("pod_monitor")


class KubernetesMonitorService:
    """Service for monitoring Kubernetes pods and nodes."""

    def __init__(self, kubeconfig_path: Optional[str] = None) -> None:
        """Initialize the Kubernetes monitor service.

        Args:
            kubeconfig_path: Optional path to kubeconfig file
        """
        self._init_kubernetes_client(kubeconfig_path)
        self.pod_problematic_threshold = 300  # 5 minutes in seconds

    def _init_kubernetes_client(self, kubeconfig_path: Optional[str] = None) -> None:
        """Initialize the Kubernetes client.

        Args:
            kubeconfig_path: Optional path to kubeconfig file
        """
        try:
            if kubeconfig_path:
                config.load_kube_config(config_file=kubeconfig_path)
            else:
                # Try to load in-cluster config if running inside Kubernetes
                try:
                    config.load_incluster_config()
                except config.config_exception.ConfigException:
                    # Fall back to default kubeconfig
                    config.load_kube_config()

            self.core_api = client.CoreV1Api()
            log.info("Kubernetes client initialized successfully")
        except Exception as e:
            log.error(f"Failed to initialize Kubernetes client: {e}")
            raise

    def get_pods(self, namespace: str, label_selector: Optional[str] = None) -> List[PodMetric]:
        """Get pods in a namespace.

        Args:
            namespace: Namespace to get pods from
            label_selector: Label selector to filter pods (e.g. "app=nginx,environment=prod")

        Returns:
            List of PodMetric objects
        """
        log.info(
            f"Getting pods in namespace {namespace}{' with label selector: ' + label_selector if label_selector else ''}"
        )

        try:
            pods = self.core_api.list_namespaced_pod(namespace, label_selector=label_selector).items
            pod_metrics = []

            for pod in pods:
                pod_name = pod.metadata.name
                pod_status = self._get_pod_status(pod)
                node_name = pod.spec.node_name

                # Parse start time
                start_time = None
                if pod.status.start_time:
                    start_time = pod.status.start_time.replace(tzinfo=None)

                # Get container statuses
                containers = [container.name for container in pod.spec.containers]
                container_statuses = {}

                if pod.status.container_statuses:
                    for container_status in pod.status.container_statuses:
                        container_name = container_status.name
                        if container_status.state.running:
                            container_statuses[container_name] = "running"
                        elif container_status.state.waiting:
                            container_statuses[container_name] = (
                                container_status.state.waiting.reason or "waiting"
                            )
                        elif container_status.state.terminated:
                            container_statuses[container_name] = (
                                container_status.state.terminated.reason or "terminated"
                            )
                        else:
                            container_statuses[container_name] = "unknown"

                # Get pod labels
                labels = {}
                if pod.metadata.labels:
                    labels = pod.metadata.labels

                pod_metric = PodMetric(
                    name=pod_name,
                    namespace=namespace,
                    status=pod_status,
                    node_name=node_name,
                    start_time=start_time,
                    containers=containers,
                    container_statuses=container_statuses,
                    labels=labels,
                )

                pod_metrics.append(pod_metric)

            return pod_metrics

        except ApiException as e:
            log.error(f"Kubernetes API error getting pods: {e}")
            raise
        except Exception as e:
            log.error(f"Error getting pods: {e}")
            raise

    def get_nodes(self, node_names: Optional[List[str]] = None) -> List[NodeMetric]:
        """Get metrics for Kubernetes nodes.

        Args:
            node_names: Optional list of node names to filter by

        Returns:
            List of NodeMetric objects
        """
        log.info(f"Getting nodes{f' with names {node_names}' if node_names else ''}")

        try:
            nodes = self.core_api.list_node().items
            node_metrics = []

            for node in nodes:
                node_name = node.metadata.name

                # Skip if not in the specified node names
                if node_names and node_name not in node_names:
                    continue

                # Get node status
                node_status = self._get_node_status(node)

                # Get node conditions
                conditions = {}
                for condition in node.status.conditions:
                    conditions[condition.type] = condition.status == "True"

                # Get node labels
                labels = {}
                if node.metadata.labels:
                    labels = node.metadata.labels

                # Get VMware machine name if available
                vmware_machine_name = None
                if labels.get("vm-name"):
                    vmware_machine_name = labels.get("vm-name")
                elif labels.get("vsphere-vm-name"):
                    vmware_machine_name = labels.get("vsphere-vm-name")
                else:
                    # If no label is present, use the node name as the VMware guest name
                    vmware_machine_name = node_name

                node_metric = NodeMetric(
                    name=node_name,
                    status=node_status,
                    vmware_machine_name=vmware_machine_name,
                    conditions=conditions,
                    labels=labels,
                )

                node_metrics.append(node_metric)

            return node_metrics

        except ApiException as e:
            log.error(f"Kubernetes API error getting nodes: {e}")
            raise
        except Exception as e:
            log.error(f"Error getting nodes: {e}")
            raise

    def get_all_nodes(self) -> List[NodeMetric]:
        """Get all nodes in the cluster.

        Returns:
            List of NodeMetric objects
        """
        log.info("Getting all nodes in the cluster")

        try:
            nodes = self.core_api.list_node().items
            node_metrics = []

            for node in nodes:
                node_name = node.metadata.name
                node_status = self._get_node_status(node)

                # Get node labels
                labels = {}
                if node.metadata.labels:
                    labels = node.metadata.labels

                # Get VMware machine name from labels
                vmware_machine_name = None
                if "vm-name" in labels:
                    vmware_machine_name = labels["vm-name"]
                elif "vsphere-vm-name" in labels:
                    vmware_machine_name = labels["vsphere-vm-name"]
                else:
                    # Use node name as VM name if no label is present
                    vmware_machine_name = node_name

                # Parse creation timestamp
                creation_time = None
                if node.metadata.creation_timestamp:
                    creation_time = node.metadata.creation_timestamp.replace(tzinfo=None)

                # Get node conditions
                conditions = {}
                if node.status.conditions:
                    for condition in node.status.conditions:
                        conditions[condition.type] = condition.status == "True"

                node_metric = NodeMetric(
                    name=node_name,
                    status=node_status,
                    creation_time=creation_time,
                    conditions=conditions,
                    labels=labels,
                    vmware_machine_name=vmware_machine_name,
                )

                node_metrics.append(node_metric)

            return node_metrics

        except Exception as e:
            log.error(f"Error getting all nodes: {e}")
            return []

    def watch_pods(self, namespace: str, timeout_seconds: int = 60) -> List[Tuple[str, PodMetric]]:
        """Watch pods in the specified namespace for changes.

        Args:
            namespace: Namespace to watch pods in
            timeout_seconds: Timeout in seconds for the watch

        Returns:
            List of tuples containing event type and PodMetric
        """
        log.info(f"Watching pods in namespace {namespace}")

        try:
            w = watch.Watch()
            events = []

            for event in w.stream(
                self.core_api.list_namespaced_pod,
                namespace=namespace,
                timeout_seconds=timeout_seconds,
            ):
                event_type = event["type"]
                pod = event["object"]

                pod_name = pod.metadata.name
                pod_status = self._get_pod_status(pod)
                node_name = pod.spec.node_name

                # Parse start time
                start_time = None
                if pod.status.start_time:
                    start_time = pod.status.start_time.replace(tzinfo=None)

                # Get container statuses
                containers = [container.name for container in pod.spec.containers]
                container_statuses = {}

                if pod.status.container_statuses:
                    for container_status in pod.status.container_statuses:
                        container_name = container_status.name
                        if container_status.state.running:
                            container_statuses[container_name] = "running"
                        elif container_status.state.waiting:
                            container_statuses[container_name] = (
                                container_status.state.waiting.reason or "waiting"
                            )
                        elif container_status.state.terminated:
                            container_statuses[container_name] = (
                                container_status.state.terminated.reason or "terminated"
                            )
                        else:
                            container_statuses[container_name] = "unknown"

                # Get pod labels
                labels = {}
                if pod.metadata.labels:
                    labels = pod.metadata.labels

                pod_metric = PodMetric(
                    name=pod_name,
                    namespace=namespace,
                    status=pod_status,
                    node_name=node_name,
                    start_time=start_time,
                    containers=containers,
                    container_statuses=container_statuses,
                    labels=labels,
                )

                events.append((event_type, pod_metric))

            return events

        except ApiException as e:
            log.error(f"Kubernetes API error watching pods: {e}")
            raise
        except Exception as e:
            log.error(f"Error watching pods: {e}")
            raise

    def check_pod_alerts(self, pod_metrics: List[PodMetric]) -> List[str]:
        """Check for pod alerts based on pod metrics.

        Args:
            pod_metrics: List of PodMetric objects

        Returns:
            List of alert messages
        """
        alerts = []

        for pod in pod_metrics:
            # Check for problematic status
            if pod.is_problematic:
                alerts.append(
                    f"Pod {pod.name} in namespace {pod.namespace} is in {pod.status} state"
                )

            # Check for pods not in Running state for too long
            if pod.status != "Running" and pod.age and pod.age > self.pod_problematic_threshold:
                alerts.append(
                    f"Pod {pod.name} in namespace {pod.namespace} has been in {pod.status} "
                    f"state for {pod.age:.1f} seconds (threshold: {self.pod_problematic_threshold}s)"
                )

            # Check for container issues
            for container, status in pod.container_statuses.items():
                if status != "running":
                    alerts.append(
                        f"Container {container} in pod {pod.name} (namespace {pod.namespace}) "
                        f"is in {status} state"
                    )

        return alerts

    def check_node_alerts(self, node_metrics: List[NodeMetric]) -> List[str]:
        """Check for node alerts based on node metrics.

        Args:
            node_metrics: List of NodeMetric objects

        Returns:
            List of alert messages
        """
        alerts = []

        for node in node_metrics:
            # Check for problematic status
            if node.is_problematic:
                alerts.append(f"Node {node.name} is in {node.status} state")

            # Check for specific conditions
            for condition, status in node.conditions.items():
                if condition == "Ready" and not status:
                    alerts.append(f"Node {node.name} is not Ready")
                elif (
                    condition
                    in ["DiskPressure", "MemoryPressure", "PIDPressure", "NetworkUnavailable"]
                    and status
                ):
                    alerts.append(f"Node {node.name} has condition {condition}")

        return alerts

    def _get_pod_status(self, pod) -> str:
        """Get the status of a pod.

        Args:
            pod: Kubernetes Pod object

        Returns:
            Pod status string
        """
        if not pod.status or not pod.status.phase:
            return "Unknown"

        phase = pod.status.phase

        # Check for CrashLoopBackOff
        if pod.status.container_statuses:
            for container_status in pod.status.container_statuses:
                if (
                    container_status.state.waiting
                    and container_status.state.waiting.reason == "CrashLoopBackOff"
                ):
                    return "CrashLoopBackOff"

        return phase

    def _get_node_status(self, node) -> str:
        """Get the status of a node.

        Args:
            node: Kubernetes Node object

        Returns:
            Node status string
        """
        if not node.status or not node.status.conditions:
            return "Unknown"

        # Check Ready condition
        for condition in node.status.conditions:
            if condition.type == "Ready":
                return "Ready" if condition.status == "True" else "NotReady"

        return "Unknown"
