"""Test configuration and fixtures for unit tests."""

from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_kubernetes_client():
    """Mock the Kubernetes client."""
    with patch("kubernetes.client.CoreV1Api") as mock_core_api:
        yield mock_core_api


@pytest.fixture
def mock_vmware_client():
    """Mock the VMware client."""
    with patch("pyVim.connect") as mock_connect:
        yield mock_connect


@pytest.fixture
def mock_config():
    """Mock configuration."""
    mock_config = MagicMock()
    mock_config.namespaces = ["default", "kube-system"]
    mock_config.monitoring_interval = 30
    mock_config.pod_label_selectors = {"app": "nginx"}
    mock_config.monitor_all_nodes = False

    # VMware config
    mock_config.vmware = MagicMock()
    mock_config.vmware.host = "vcenter.example.com"
    mock_config.vmware.username = "admin"
    mock_config.vmware.password = "password"
    mock_config.vmware.port = 443
    mock_config.vmware.disable_ssl_verification = True

    return mock_config


@pytest.fixture
def sample_pod_list():
    """Sample pod list for testing."""
    pod1 = MagicMock()
    pod1.metadata.name = "test-pod-1"
    pod1.metadata.namespace = "default"
    pod1.metadata.labels = {"app": "nginx"}
    pod1.spec.node_name = "node-1"
    pod1.status.phase = "Running"
    pod1.status.start_time = None

    container_status1 = MagicMock()
    container_status1.name = "nginx"
    container_status1.state.running = True
    container_status1.state.waiting = None
    container_status1.state.terminated = None

    pod1.status.container_statuses = [container_status1]

    container1 = MagicMock()
    container1.name = "nginx"
    pod1.spec.containers = [container1]

    pod2 = MagicMock()
    pod2.metadata.name = "test-pod-2"
    pod2.metadata.namespace = "default"
    pod2.metadata.labels = {"app": "nginx"}
    pod2.spec.node_name = "node-2"
    pod2.status.phase = "Pending"
    pod2.status.start_time = None

    container_status2 = MagicMock()
    container_status2.name = "nginx"
    container_status2.state.running = None
    container_status2.state.waiting = MagicMock()
    container_status2.state.waiting.reason = "ContainerCreating"
    container_status2.state.terminated = None

    pod2.status.container_statuses = [container_status2]

    container2 = MagicMock()
    container2.name = "nginx"
    pod2.spec.containers = [container2]

    return [pod1, pod2]


@pytest.fixture
def sample_node_list():
    """Sample node list for testing."""
    node1 = MagicMock()
    node1.metadata.name = "node-1"
    node1.metadata.labels = {"vm-name": "vm-node-1"}

    condition1 = MagicMock()
    condition1.type = "Ready"
    condition1.status = "True"

    condition2 = MagicMock()
    condition2.type = "DiskPressure"
    condition2.status = "False"

    node1.status.conditions = [condition1, condition2]

    node2 = MagicMock()
    node2.metadata.name = "node-2"
    node2.metadata.labels = {"vsphere-vm-name": "vm-node-2"}

    condition3 = MagicMock()
    condition3.type = "Ready"
    condition3.status = "False"

    condition4 = MagicMock()
    condition4.type = "DiskPressure"
    condition4.status = "True"

    node2.status.conditions = [condition3, condition4]

    return [node1, node2]


@pytest.fixture
def sample_vmware_vms():
    """Sample VMware VMs for testing."""
    vm1 = MagicMock()
    vm1.name = "vm-node-1"
    vm1.runtime.powerState = "poweredOn"
    vm1.summary.quickStats.overallCpuUsage = 1000
    vm1.summary.quickStats.guestMemoryUsage = 4096
    vm1.summary.config.numCpu = 4
    vm1.summary.config.memorySizeMB = 8192

    vm2 = MagicMock()
    vm2.name = "vm-node-2"
    vm2.runtime.powerState = "poweredOff"
    vm2.summary.quickStats.overallCpuUsage = 0
    vm2.summary.quickStats.guestMemoryUsage = 0
    vm2.summary.config.numCpu = 4
    vm2.summary.config.memorySizeMB = 8192

    return [vm1, vm2]


@pytest.fixture
def sample_crd_object():
    """Sample CRD object for testing."""
    crd = {
        "apiVersion": "monitoring.k8s.playground/v1",
        "kind": "PodMonitor",
        "metadata": {"name": "test-pod-monitor", "namespace": "default"},
        "spec": {
            "namespaces": ["default", "kube-system"],
            "labelSelector": {"matchLabels": {"app": "nginx"}},
            "interval": 30,
            "vmwareIntegration": {"enabled": True, "host": "vcenter.example.com", "port": 443},
        },
    }
    return crd
