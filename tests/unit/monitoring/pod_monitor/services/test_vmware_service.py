"""Unit tests for the VMware service."""

from unittest.mock import ANY, MagicMock, patch

import pytest

from apps.monitoring.pod_monitor.models.metrics import VMwareMetric
from apps.monitoring.pod_monitor.services.vmware_service import VMwareMonitorService


class TestVMwareMonitorService:
    """Tests for the VMwareMonitorService class."""

    def test_init(self, mock_vmware_client):
        """Test initialization of the VMware monitor service."""
        with patch("pyVim.connect.SmartConnect") as mock_smart_connect:
            mock_content = MagicMock()
            mock_service_instance = MagicMock()
            mock_service_instance.RetrieveContent.return_value = mock_content
            mock_smart_connect.return_value = mock_service_instance

            # Create service
            service = VMwareMonitorService(
                host="vcenter.example.com",
                username="admin",
                password="password",
                port=443,
                disable_ssl_verification=True,
            )

            # Verify connection was established
            mock_smart_connect.assert_called_once_with(
                host="vcenter.example.com",
                user="admin",
                pwd="password",
                port=443,
                sslContext=ANY,
            )

            # Verify content was retrieved
            mock_service_instance.RetrieveContent.assert_called_once()

            # Verify service instance and content were stored
            assert service.service_instance == mock_service_instance
            assert service.content == mock_content

    def test_connect(self, mock_vmware_client):
        """Test connecting to VMware."""
        with patch("pyVim.connect.SmartConnect") as mock_smart_connect:
            mock_content = MagicMock()
            mock_service_instance = MagicMock()
            mock_service_instance.RetrieveContent.return_value = mock_content
            mock_smart_connect.return_value = mock_service_instance

            # Create service with connect disabled
            service = VMwareMonitorService(
                host="vcenter.example.com",
                username="admin",
                password="password",
                port=443,
                disable_ssl_verification=True,
            )

            # Reset mock
            mock_smart_connect.reset_mock()
            mock_service_instance.RetrieveContent.reset_mock()

            # Call connect
            service._connect()

            # Verify connection was established
            mock_smart_connect.assert_called_once_with(
                host="vcenter.example.com",
                user="admin",
                pwd="password",
                port=443,
                sslContext=ANY,
            )

            # Verify content was retrieved
            mock_service_instance.RetrieveContent.assert_called_once()

    def test_disconnect(self, mock_vmware_client):
        """Test disconnecting from VMware."""
        with patch("pyVim.connect.SmartConnect") as mock_smart_connect:
            with patch("pyVim.connect.Disconnect") as mock_disconnect:
                mock_content = MagicMock()
                mock_service_instance = MagicMock()
                mock_service_instance.RetrieveContent.return_value = mock_content
                mock_smart_connect.return_value = mock_service_instance

                # Create service
                service = VMwareMonitorService(
                    host="vcenter.example.com",
                    username="admin",
                    password="password",
                    port=443,
                    disable_ssl_verification=True,
                )

                # Call disconnect
                service._disconnect()

                # Verify disconnect was called
                mock_disconnect.assert_called_once_with(mock_service_instance)

    def test_get_all_vms(self, mock_vmware_client, sample_vmware_vms):
        """Test getting all VMs."""
        with patch("pyVim.connect.SmartConnect") as mock_smart_connect:
            mock_content = MagicMock()
            mock_service_instance = MagicMock()
            mock_service_instance.RetrieveContent.return_value = mock_content
            mock_smart_connect.return_value = mock_service_instance

            # Setup mock view manager
            mock_view_manager = MagicMock()
            mock_content.viewManager = mock_view_manager

            # Setup mock container view
            mock_container_view = MagicMock()
            mock_view_manager.CreateContainerView.return_value = mock_container_view
            mock_container_view.view = sample_vmware_vms

            # Create service
            service = VMwareMonitorService(
                host="vcenter.example.com",
                username="admin",
                password="password",
                port=443,
                disable_ssl_verification=True,
            )

            # Get all VMs - use private method since there's no public method
            container = service.content.viewManager.CreateContainerView(
                service.content.rootFolder, [MagicMock()], True
            )
            vms = container.view

            # Verify container view was created
            mock_view_manager.CreateContainerView.assert_called_once()

            # Verify VMs were returned
            assert len(vms) == len(sample_vmware_vms)
            assert vms == sample_vmware_vms

    def test_get_vm_by_name(self, mock_vmware_client, sample_vmware_vms):
        """Test getting a VM by name."""
        with patch("pyVim.connect.SmartConnect") as mock_smart_connect:
            mock_content = MagicMock()
            mock_service_instance = MagicMock()
            mock_service_instance.RetrieveContent.return_value = mock_content
            mock_smart_connect.return_value = mock_service_instance

            # Setup mock view manager
            mock_view_manager = MagicMock()
            mock_content.viewManager = mock_view_manager

            # Setup mock container view
            mock_container_view = MagicMock()
            mock_view_manager.CreateContainerView.return_value = mock_container_view
            mock_container_view.view = sample_vmware_vms

            # Set the name of the first VM
            sample_vmware_vms[0].name = "vm-1"

            # Create service
            service = VMwareMonitorService(
                host="vcenter.example.com",
                username="admin",
                password="password",
                port=443,
                disable_ssl_verification=True,
            )

            # Get VM by name
            vm = service._get_vm_by_name("vm-1")

            # Verify container view was created
            mock_view_manager.CreateContainerView.assert_called_once()

            # Verify VM was returned
            assert vm == sample_vmware_vms[0]

    def test_get_vm_metrics(self, mock_vmware_client, sample_vmware_vms):
        """Test getting VM metrics."""
        with patch("pyVim.connect.SmartConnect") as mock_smart_connect:
            mock_content = MagicMock()
            mock_service_instance = MagicMock()
            mock_service_instance.RetrieveContent.return_value = mock_content
            mock_smart_connect.return_value = mock_service_instance

            # Setup mock VM properties
            sample_vmware_vms[0].name = "vm-1"
            sample_vmware_vms[0].summary.config.name = "vm-1"
            sample_vmware_vms[0].summary.quickStats.overallCpuUsage = 1000
            sample_vmware_vms[0].summary.quickStats.hostMemoryUsage = 2048
            sample_vmware_vms[0].summary.config.memorySizeMB = 4096
            sample_vmware_vms[0].summary.config.numCpu = 2
            sample_vmware_vms[0].runtime.powerState = "poweredOn"

            sample_vmware_vms[1].name = "vm-2"
            sample_vmware_vms[1].summary.config.name = "vm-2"
            sample_vmware_vms[1].summary.quickStats.overallCpuUsage = 2000
            sample_vmware_vms[1].summary.quickStats.hostMemoryUsage = 4096
            sample_vmware_vms[1].summary.config.memorySizeMB = 8192
            sample_vmware_vms[1].summary.config.numCpu = 4
            sample_vmware_vms[1].runtime.powerState = "poweredOff"

            # Create service
            service = VMwareMonitorService(
                host="vcenter.example.com",
                username="admin",
                password="password",
                port=443,
                disable_ssl_verification=True,
            )

            # Mock the _get_vm_by_name method to return the sample VMs
            with patch.object(service, "_get_vm_by_name") as mock_get_vm:
                mock_get_vm.side_effect = lambda name: (
                    sample_vmware_vms[0] if name == "vm-1" else sample_vmware_vms[1]
                )

                # Get VM metrics
                metrics = service.get_vm_metrics(["vm-1", "vm-2"], ["node-1", "node-2"])

                # Verify _get_vm_by_name was called for each VM
                assert mock_get_vm.call_count == 2

                # Verify metrics were returned
                assert len(metrics) == 2
                assert isinstance(metrics[0], VMwareMetric)
                assert metrics[0].name == "vm-1"
                assert metrics[0].status == "poweredOn"
                assert metrics[0].node_name == "node-1"

    def test_check_vm_alerts(self):
        """Test checking VM alerts."""
        # Create VM metrics
        vm1 = VMwareMetric(
            name="vm-1",
            status="poweredOn",
            node_name="node-1",
            cpu_usage=1000,
            memory_usage=2048,
            cpu_capacity=4000,
            memory_capacity=4096,
        )
        vm2 = VMwareMetric(
            name="vm-2",
            status="poweredOff",
            node_name="node-2",
            cpu_usage=2000,
            memory_usage=4096,
            cpu_capacity=8000,
            memory_capacity=8192,
        )

        # Use patch to avoid actual connection
        with patch("pyVim.connect.SmartConnect") as mock_smart_connect:
            mock_content = MagicMock()
            mock_service_instance = MagicMock()
            mock_service_instance.RetrieveContent.return_value = mock_content
            mock_smart_connect.return_value = mock_service_instance

            # Check alerts
            service = VMwareMonitorService(
                host="vcenter.example.com",
                username="admin",
                password="password",
                port=443,
                disable_ssl_verification=True,
            )
            alerts = service.check_vm_alerts([vm1, vm2])

            # Verify alerts
            assert len(alerts) == 1
            assert "VMware machine vm-2 (node node-2) is in poweredOff state" == alerts[0]
