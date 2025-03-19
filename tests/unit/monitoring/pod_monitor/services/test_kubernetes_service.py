"""Unit tests for the Kubernetes service."""

from unittest.mock import MagicMock, patch

import pytest
from kubernetes.client.exceptions import ApiException

from apps.monitoring.pod_monitor.models.metrics import NodeMetric, PodMetric
from apps.monitoring.pod_monitor.services.kubernetes_service import KubernetesMonitorService


class TestKubernetesMonitorService:
    """Tests for the KubernetesMonitorService class."""

    def test_init(self, mock_kubernetes_client):
        """Test initialization of the Kubernetes monitor service."""
        # Test with default kubeconfig
        with patch("kubernetes.config.load_kube_config") as mock_load_kube_config:
            with patch("kubernetes.config.load_incluster_config") as mock_load_incluster_config:
                mock_load_incluster_config.side_effect = Exception("Not in cluster")

                service = KubernetesMonitorService()

                # Verify that load_incluster_config was attempted first
                mock_load_incluster_config.assert_called_once()

                # Verify that load_kube_config was called as fallback
                mock_load_kube_config.assert_called_once()

                # Verify that the core API was initialized
                assert hasattr(service, "core_api")

        # Test with custom kubeconfig
        with patch("kubernetes.config.load_kube_config") as mock_load_kube_config:
            service = KubernetesMonitorService(kubeconfig_path="/path/to/kubeconfig")

            # Verify that load_kube_config was called with the custom path
            mock_load_kube_config.assert_called_once_with(config_file="/path/to/kubeconfig")

            # Verify that the core API was initialized
            assert hasattr(service, "core_api")

    def test_get_pods(self, mock_kubernetes_client, sample_pod_list):
        """Test getting pods from a namespace."""
        # Setup mock
        mock_api_instance = mock_kubernetes_client.return_value
        mock_pod_list = MagicMock()
        mock_pod_list.items = sample_pod_list
        mock_api_instance.list_namespaced_pod.return_value = mock_pod_list

        # Create service
        service = KubernetesMonitorService()
        service.core_api = mock_api_instance

        # Call method
        pods = service.get_pods("default", label_selector="app=nginx")

        # Verify API call
        mock_api_instance.list_namespaced_pod.assert_called_once_with(
            "default", label_selector="app=nginx"
        )

        # Verify results
        assert len(pods) == 2
        assert pods[0].name == "test-pod-1"
        assert pods[0].namespace == "default"
        assert pods[0].status == "Running"
        assert pods[0].node_name == "node-1"
        assert pods[0].container_statuses == {"nginx": "running"}

        assert pods[1].name == "test-pod-2"
        assert pods[1].namespace == "default"
        assert pods[1].status == "Pending"
        assert pods[1].node_name == "node-2"
        assert pods[1].container_statuses == {"nginx": "ContainerCreating"}

    def test_get_pods_api_exception(self, mock_kubernetes_client):
        """Test handling of API exceptions when getting pods."""
        # Setup mock
        mock_api_instance = mock_kubernetes_client.return_value
        mock_api_instance.list_namespaced_pod.side_effect = ApiException(
            status=404, reason="Not Found"
        )

        # Create service
        service = KubernetesMonitorService()
        service.core_api = mock_api_instance

        # Call method and verify exception
        with pytest.raises(ApiException):
            service.get_pods("default")

        # Verify API call
        mock_api_instance.list_namespaced_pod.assert_called_once_with(
            "default", label_selector=None
        )

    def test_get_nodes(self, mock_kubernetes_client, sample_node_list):
        """Test getting nodes."""
        # Setup mock
        mock_api_instance = mock_kubernetes_client.return_value
        mock_node_list = MagicMock()
        mock_node_list.items = sample_node_list
        mock_api_instance.list_node.return_value = mock_node_list

        # Create service
        service = KubernetesMonitorService()
        service.core_api = mock_api_instance

        # Call method
        nodes = service.get_nodes(node_names=["node-1"])

        # Verify API call
        mock_api_instance.list_node.assert_called_once()

        # Verify results
        assert len(nodes) == 1
        assert nodes[0].name == "node-1"
        assert nodes[0].vmware_machine_name == "vm-node-1"
        assert nodes[0].conditions == {"Ready": True, "DiskPressure": False}

    def test_get_all_nodes(self, mock_kubernetes_client, sample_node_list):
        """Test getting all nodes."""
        # Setup mock
        mock_api_instance = mock_kubernetes_client.return_value
        mock_node_list = MagicMock()
        mock_node_list.items = sample_node_list
        mock_api_instance.list_node.return_value = mock_node_list

        # Create service
        service = KubernetesMonitorService()
        service.core_api = mock_api_instance

        # Call method
        nodes = service.get_all_nodes()

        # Verify API call
        mock_api_instance.list_node.assert_called_once()

        # Verify results
        assert len(nodes) == 2
        assert nodes[0].name == "node-1"
        assert nodes[1].name == "node-2"

    def test_check_pod_alerts(self):
        """Test checking for pod alerts."""
        # Create test pod metrics
        pod1 = PodMetric(
            name="test-pod-1",
            namespace="default",
            status="Running",
            node_name="node-1",
            container_statuses={"nginx": "running"},
        )

        pod2 = PodMetric(
            name="test-pod-2",
            namespace="default",
            status="Pending",
            node_name="node-2",
            container_statuses={"nginx": "waiting"},
        )

        pod3 = PodMetric(
            name="test-pod-3",
            namespace="default",
            status="CrashLoopBackOff",
            node_name="node-1",
            container_statuses={"nginx": "error"},
        )

        # Create service
        service = KubernetesMonitorService()

        # Call method
        alerts = service.check_pod_alerts([pod1, pod2, pod3])

        # Verify results
        assert len(alerts) == 4
        assert "Pod test-pod-2 in namespace default is in Pending state" in alerts
        assert "Container nginx in pod test-pod-2 (namespace default) is in waiting state" in alerts
        assert "Pod test-pod-3 in namespace default is in CrashLoopBackOff state" in alerts
        assert "Container nginx in pod test-pod-3 (namespace default) is in error state" in alerts

    def test_check_node_alerts(self):
        """Test checking for node alerts."""
        # Create test node metrics
        node1 = NodeMetric(
            name="node-1",
            status="Ready",
            vmware_machine_name="vm-node-1",
            conditions={"Ready": True, "DiskPressure": False},
        )

        node2 = NodeMetric(
            name="node-2",
            status="NotReady",
            vmware_machine_name="vm-node-2",
            conditions={"Ready": False, "DiskPressure": True},
        )

        # Create service
        service = KubernetesMonitorService()

        # Call method
        alerts = service.check_node_alerts([node1, node2])

        # Verify results
        assert len(alerts) == 3
        assert "Node node-2 is in NotReady state" in alerts
        assert "Node node-2 is not Ready" in alerts
        assert "Node node-2 has condition DiskPressure" in alerts

    def test_watch_pods(self, mock_kubernetes_client):
        """Test watching for pod events."""
        # Setup mock
        mock_api_instance = mock_kubernetes_client.return_value

        with patch("kubernetes.watch.Watch") as mock_watch:
            # Create mock pod objects
            pod1 = MagicMock()
            pod1.metadata.name = "test-pod-1"
            pod1.metadata.namespace = "default"
            pod1.status.phase = "Running"
            pod1.spec.node_name = "node-1"
            pod1.spec.containers = []
            pod1.status.container_statuses = None
            pod1.metadata.labels = {}
            pod1.status.start_time = None

            pod2 = MagicMock()
            pod2.metadata.name = "test-pod-2"
            pod2.metadata.namespace = "default"
            pod2.status.phase = "Running"
            pod2.spec.node_name = "node-2"
            pod2.spec.containers = []
            pod2.status.container_statuses = None
            pod2.metadata.labels = {}
            pod2.status.start_time = None

            pod3 = MagicMock()
            pod3.metadata.name = "test-pod-3"
            pod3.metadata.namespace = "default"
            pod3.status.phase = "Succeeded"
            pod3.spec.node_name = "node-1"
            pod3.spec.containers = []
            pod3.status.container_statuses = None
            pod3.metadata.labels = {}
            pod3.status.start_time = None

            # Setup mock watch stream
            mock_watch_instance = mock_watch.return_value
            mock_watch_instance.stream.return_value = [
                {"type": "ADDED", "object": pod1},
                {"type": "MODIFIED", "object": pod2},
                {"type": "DELETED", "object": pod3},
            ]

            # Create service
            service = KubernetesMonitorService()
            service.core_api = mock_api_instance

            # Create callback function
            callback = MagicMock()

            # Call method
            service.watch_pods("default", callback, timeout_seconds=10)

            # Verify watch was created
            mock_watch.assert_called_once()
            mock_watch_instance.stream.assert_called_once_with(
                service.core_api.list_namespaced_pod, namespace="default", timeout_seconds=10
            )

            # Verify callback was called for each event
            assert callback.call_count == 3

            # Check that the callback was called with PodMetric objects
            for i, call_args in enumerate(callback.call_args_list):
                event_type, pod_metric = call_args[0]
                assert isinstance(pod_metric, PodMetric)

                # Verify event type
                expected_event_type = mock_watch_instance.stream.return_value[i]["type"]
                assert event_type == expected_event_type

                # Verify pod name
                expected_pod = mock_watch_instance.stream.return_value[i]["object"]
                assert pod_metric.name == expected_pod.metadata.name
                assert pod_metric.namespace == expected_pod.metadata.namespace
                assert pod_metric.status == expected_pod.status.phase

    def test_watch_nodes(self, mock_kubernetes_client):
        """Test watching for node events."""
        # Setup mock
        mock_api_instance = mock_kubernetes_client.return_value

        with patch("kubernetes.watch.Watch") as mock_watch:
            # Create mock node objects
            node1 = MagicMock()
            node1.metadata.name = "node-1"
            node1.metadata.labels = {}
            ready_condition1 = MagicMock()
            ready_condition1.type = "Ready"
            ready_condition1.status = "True"
            node1.status.conditions = [ready_condition1]

            node2 = MagicMock()
            node2.metadata.name = "node-2"
            node2.metadata.labels = {}
            ready_condition2 = MagicMock()
            ready_condition2.type = "Ready"
            ready_condition2.status = "False"
            node2.status.conditions = [ready_condition2]

            # Setup mock watch stream
            mock_watch_instance = mock_watch.return_value
            mock_watch_instance.stream.return_value = [
                {"type": "ADDED", "object": node1},
                {"type": "MODIFIED", "object": node2},
            ]

            # Create service
            service = KubernetesMonitorService()
            service.core_api = mock_api_instance

            # Create callback function
            callback = MagicMock()

            # Call method
            service.watch_nodes(callback, timeout_seconds=10)

            # Verify watch was created
            mock_watch.assert_called_once()
            mock_watch_instance.stream.assert_called_once_with(
                service.core_api.list_node, timeout_seconds=10
            )

            # Verify callback was called for each event
            assert callback.call_count == 2

            # Check that the callback was called with NodeMetric objects
            for i, call_args in enumerate(callback.call_args_list):
                event_type, node_metric = call_args[0]
                assert isinstance(node_metric, NodeMetric)

                # Verify event type
                expected_event_type = mock_watch_instance.stream.return_value[i]["type"]
                assert event_type == expected_event_type

                # Verify node name
                expected_node = mock_watch_instance.stream.return_value[i]["object"]
                assert node_metric.name == expected_node.metadata.name

                # Verify status based on Ready condition
                ready_condition = expected_node.status.conditions[0]
                expected_status = "Ready" if ready_condition.status == "True" else "NotReady"
                assert node_metric.status == expected_status
