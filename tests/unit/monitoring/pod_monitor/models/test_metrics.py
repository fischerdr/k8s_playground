"""Unit tests for the metrics models."""

from datetime import datetime, timedelta

import pytest

from apps.monitoring.pod_monitor.models.metrics import (
    NodeMetric,
    NodeStatus,
    PodMetric,
    PodStatus,
    VMwareMetric,
    VMwareStatus,
)


class TestPodStatus:
    """Tests for the PodStatus enum."""

    def test_is_problematic(self):
        """Test the is_problematic method."""
        # Problematic statuses
        assert PodStatus.is_problematic("Pending") is True
        assert PodStatus.is_problematic("Failed") is True
        assert PodStatus.is_problematic("Unknown") is True
        assert PodStatus.is_problematic("CrashLoopBackOff") is True

        # Non-problematic statuses
        assert PodStatus.is_problematic("Running") is False
        assert PodStatus.is_problematic("Succeeded") is False


class TestNodeStatus:
    """Tests for the NodeStatus enum."""

    def test_is_problematic(self):
        """Test the is_problematic method."""
        # Problematic statuses
        assert NodeStatus.is_problematic("NotReady") is True
        assert NodeStatus.is_problematic("Unknown") is True

        # Non-problematic statuses
        assert NodeStatus.is_problematic("Ready") is False


class TestVMwareStatus:
    """Tests for the VMwareStatus enum."""

    def test_is_problematic(self):
        """Test the is_problematic method."""
        # Problematic statuses
        assert VMwareStatus.is_problematic("poweredOff") is True
        assert VMwareStatus.is_problematic("suspended") is True
        assert VMwareStatus.is_problematic("disconnected") is True

        # Non-problematic statuses
        assert VMwareStatus.is_problematic("poweredOn") is False


class TestPodMetric:
    """Tests for the PodMetric class."""

    def test_age(self):
        """Test the age property."""
        # Create pod with start time
        start_time = datetime.now() - timedelta(hours=1)
        pod = PodMetric(
            name="test-pod", namespace="default", status="Running", start_time=start_time
        )

        # Verify age is approximately 1 hour
        assert pod.age is not None
        assert 3500 < pod.age < 3700  # Between 58 and 62 minutes in seconds

        # Create pod without start time
        pod = PodMetric(name="test-pod", namespace="default", status="Running")

        # Verify age is None
        assert pod.age is None

    def test_is_problematic(self):
        """Test the is_problematic property."""
        # Create problematic pod
        pod = PodMetric(name="test-pod", namespace="default", status="Pending")

        # Verify is_problematic is True
        assert pod.is_problematic is True

        # Create non-problematic pod
        pod = PodMetric(name="test-pod", namespace="default", status="Running")

        # Verify is_problematic is False
        assert pod.is_problematic is False

    def test_to_prometheus(self):
        """Test the to_prometheus method."""
        # Create pod with node and containers
        pod = PodMetric(
            name="test-pod",
            namespace="default",
            status="Running",
            node_name="node-1",
            start_time=datetime.now() - timedelta(hours=1),
            container_statuses={"nginx": "running", "sidecar": "waiting"},
        )

        # Get Prometheus metrics
        metrics = pod.to_prometheus()

        # Verify metrics
        assert len(metrics) == 4
        assert (
            'k8s_pod_status{namespace="default",pod="test-pod",status="Running",node="node-1"} 1'
            in metrics
        )
        assert (
            'k8s_container_status{namespace="default",pod="test-pod",container="nginx",status="running"} 1'
            in metrics
        )
        assert (
            'k8s_container_status{namespace="default",pod="test-pod",container="sidecar",status="waiting"} 0'
            in metrics
        )
        assert (
            'k8s_pod_age_seconds{namespace="default",pod="test-pod",status="Running",node="node-1"}'
            in metrics[3]
        )


class TestNodeMetric:
    """Tests for the NodeMetric class."""

    def test_is_problematic(self):
        """Test the is_problematic property."""
        # Create problematic node
        node = NodeMetric(name="node-1", status="NotReady")

        # Verify is_problematic is True
        assert node.is_problematic is True

        # Create non-problematic node
        node = NodeMetric(name="node-1", status="Ready")

        # Verify is_problematic is False
        assert node.is_problematic is False

    def test_to_prometheus(self):
        """Test the to_prometheus method."""
        # Create node with conditions
        node = NodeMetric(
            name="node-1",
            status="Ready",
            vmware_machine_name="vm-node-1",
            conditions={"Ready": True, "DiskPressure": False},
        )

        # Get Prometheus metrics
        metrics = node.to_prometheus()

        # Verify metrics
        assert len(metrics) == 3
        assert (
            'k8s_node_status{node="node-1",status="Ready",vmware_machine="vm-node-1"} 1' in metrics
        )
        assert 'k8s_node_condition{node="node-1",condition="Ready"} 1' in metrics
        assert 'k8s_node_condition{node="node-1",condition="DiskPressure"} 0' in metrics


class TestVMwareMetric:
    """Tests for the VMwareMetric class."""

    def test_is_problematic(self):
        """Test the is_problematic property."""
        # Create problematic VM
        vm = VMwareMetric(name="vm-node-1", status="poweredOff", node_name="node-1")

        # Verify is_problematic is True
        assert vm.is_problematic is True

        # Create non-problematic VM
        vm = VMwareMetric(name="vm-node-1", status="poweredOn", node_name="node-1")

        # Verify is_problematic is False
        assert vm.is_problematic is False

    def test_cpu_percent(self):
        """Test the cpu_percent property."""
        # Create VM with CPU metrics
        vm = VMwareMetric(
            name="vm-node-1",
            status="poweredOn",
            node_name="node-1",
            cpu_usage=1000,
            cpu_capacity=4000,
        )

        # Verify CPU percent
        assert vm.cpu_percent == 25.0

        # Create VM without CPU metrics
        vm = VMwareMetric(name="vm-node-1", status="poweredOn", node_name="node-1")

        # Verify CPU percent is None
        assert vm.cpu_percent is None

    def test_memory_percent(self):
        """Test the memory_percent property."""
        # Create VM with memory metrics
        vm = VMwareMetric(
            name="vm-node-1",
            status="poweredOn",
            node_name="node-1",
            memory_usage=2048,
            memory_capacity=8192,
        )

        # Verify memory percent
        assert vm.memory_percent == 25.0

        # Create VM without memory metrics
        vm = VMwareMetric(name="vm-node-1", status="poweredOn", node_name="node-1")

        # Verify memory percent is None
        assert vm.memory_percent is None

    def test_to_prometheus(self):
        """Test the to_prometheus method."""
        # Create VM with all metrics
        vm = VMwareMetric(
            name="vm-node-1",
            status="poweredOn",
            node_name="node-1",
            cpu_usage=1000,
            memory_usage=2048,
            cpu_capacity=4000,
            memory_capacity=8192,
        )

        # Get Prometheus metrics
        metrics = vm.to_prometheus()

        # Verify metrics
        assert len(metrics) == 5
        assert (
            'vmware_machine_status{vmware_machine="vm-node-1",status="poweredOn",node="node-1"} 1'
            in metrics
        )
        assert 'vmware_machine_cpu_usage{vmware_machine="vm-node-1",node="node-1"} 1000' in metrics
        assert (
            'vmware_machine_memory_usage{vmware_machine="vm-node-1",node="node-1"} 2048' in metrics
        )
        assert (
            'vmware_machine_cpu_percent{vmware_machine="vm-node-1",node="node-1"} 25.0' in metrics
        )
        assert (
            'vmware_machine_memory_percent{vmware_machine="vm-node-1",node="node-1"} 25.0'
            in metrics
        )
