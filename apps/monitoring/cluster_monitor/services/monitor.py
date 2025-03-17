"""Cluster monitoring service.

This module provides services for monitoring Kubernetes cluster resources.
"""

import logging
from typing import Dict, List, Optional

from kubernetes import client, config
from kubernetes.client.exceptions import ApiException

from ..models.cluster import ClusterMetrics, NodeMetrics
from ..utils.config import Config

log = logging.getLogger("cluster_monitor")


class ClusterMonitorService:
    """Service for monitoring Kubernetes cluster resources."""

    def __init__(self, config_data: Config) -> None:
        """Initialize the cluster monitor service.

        Args:
            config_data: Configuration data for the service
        """
        self.config = config_data
        self._init_kubernetes_client()

    def _init_kubernetes_client(self) -> None:
        """Initialize the Kubernetes client."""
        try:
            if self.config.kubeconfig_path:
                config.load_kube_config(config_file=self.config.kubeconfig_path)
            else:
                # Try to load in-cluster config if running inside Kubernetes
                try:
                    config.load_incluster_config()
                except config.config_exception.ConfigException:
                    # Fall back to default kubeconfig
                    config.load_kube_config()

            self.core_api = client.CoreV1Api()
            self.metrics_api = client.CustomObjectsApi()
            log.info("Kubernetes client initialized successfully")
        except Exception as e:
            log.error(f"Failed to initialize Kubernetes client: {e}")
            raise

    def collect_metrics(self, namespace: Optional[str] = None) -> ClusterMetrics:
        """Collect metrics from the Kubernetes cluster.

        Args:
            namespace: Optional namespace to filter metrics

        Returns:
            ClusterMetrics object containing collected metrics
        """
        log.info(f"Collecting metrics{f' for namespace {namespace}' if namespace else ''}")

        try:
            # Get nodes
            nodes = self.core_api.list_node().items

            # Get node metrics
            node_metrics_list = self.metrics_api.list_cluster_custom_object(
                group="metrics.k8s.io",
                version="v1beta1",
                plural="nodes",
            ).get("items", [])

            # Create a dictionary for quick lookup
            node_metrics_dict = {
                item["metadata"]["name"]: item["usage"] for item in node_metrics_list
            }

            # Get pods
            if namespace:
                pods = self.core_api.list_namespaced_pod(namespace).items
                total_pods = len(pods)
            else:
                pods = self.core_api.list_pod_for_all_namespaces().items
                total_pods = len(pods)

            # Count pods per node
            pods_per_node: Dict[str, int] = {}
            for pod in pods:
                node_name = pod.spec.node_name
                if node_name:
                    pods_per_node[node_name] = pods_per_node.get(node_name, 0) + 1

            # Process node metrics
            node_metrics_list = []
            healthy_nodes = 0

            for node in nodes:
                node_name = node.metadata.name

                # Get node metrics
                node_usage = node_metrics_dict.get(node_name, {})
                cpu_usage = self._parse_cpu(node_usage.get("cpu", "0"))
                memory_usage = self._parse_memory(node_usage.get("memory", "0"))

                # Get node capacity
                cpu_capacity = self._parse_cpu(node.status.capacity.get("cpu", "0"))
                memory_capacity = self._parse_memory(node.status.capacity.get("memory", "0"))

                # Get node conditions
                conditions = {}
                for condition in node.status.conditions:
                    conditions[condition.type] = condition.status == "True"

                # Check if node is healthy
                if conditions.get("Ready", False):
                    healthy_nodes += 1

                # Create node metrics
                node_metrics = NodeMetrics(
                    name=node_name,
                    cpu_usage=cpu_usage,
                    memory_usage=memory_usage,
                    cpu_capacity=cpu_capacity,
                    memory_capacity=memory_capacity,
                    pods_running=pods_per_node.get(node_name, 0),
                    conditions=conditions,
                )

                node_metrics_list.append(node_metrics)

            # Create cluster metrics
            cluster_metrics = ClusterMetrics(
                nodes=node_metrics_list,
                total_nodes=len(nodes),
                healthy_nodes=healthy_nodes,
                total_pods=total_pods,
                namespace=namespace,
            )

            return cluster_metrics

        except ApiException as e:
            log.error(f"Kubernetes API error: {e}")
            raise
        except Exception as e:
            log.error(f"Error collecting metrics: {e}")
            raise

    def _parse_cpu(self, cpu_str: str) -> float:
        """Parse CPU string to float value in cores.

        Args:
            cpu_str: CPU string (e.g., "100m" for 0.1 cores)

        Returns:
            CPU value in cores
        """
        if cpu_str.endswith("m"):
            return float(cpu_str[:-1]) / 1000
        return float(cpu_str)

    def _parse_memory(self, memory_str: str) -> float:
        """Parse memory string to float value in bytes.

        Args:
            memory_str: Memory string (e.g., "1Gi" for 1 gibibyte)

        Returns:
            Memory value in bytes
        """
        if memory_str.endswith("Ki"):
            return float(memory_str[:-2]) * 1024
        elif memory_str.endswith("Mi"):
            return float(memory_str[:-2]) * 1024 * 1024
        elif memory_str.endswith("Gi"):
            return float(memory_str[:-2]) * 1024 * 1024 * 1024
        elif memory_str.endswith("Ti"):
            return float(memory_str[:-2]) * 1024 * 1024 * 1024 * 1024
        elif memory_str.endswith("Pi"):
            return float(memory_str[:-2]) * 1024 * 1024 * 1024 * 1024 * 1024
        elif memory_str.endswith("k") or memory_str.endswith("K"):
            return float(memory_str[:-1]) * 1000
        elif memory_str.endswith("m") or memory_str.endswith("M"):
            return float(memory_str[:-1]) * 1000 * 1000
        elif memory_str.endswith("g") or memory_str.endswith("G"):
            return float(memory_str[:-1]) * 1000 * 1000 * 1000
        elif memory_str.endswith("t") or memory_str.endswith("T"):
            return float(memory_str[:-1]) * 1000 * 1000 * 1000 * 1000
        elif memory_str.endswith("p") or memory_str.endswith("P"):
            return float(memory_str[:-1]) * 1000 * 1000 * 1000 * 1000 * 1000
        return float(memory_str)
