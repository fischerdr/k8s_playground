"""VMware monitoring service.

This module provides services for monitoring VMware machines.
"""

import logging
import ssl
from typing import Dict, List, Optional

from pyVim import connect
from pyVmomi import vim

from ..models.metrics import VMwareMetric

log = logging.getLogger("pod_monitor")


class VMwareMonitorService:
    """Service for monitoring VMware machines."""

    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        port: int = 443,
        disable_ssl_verification: bool = False,
    ) -> None:
        """Initialize the VMware monitor service.

        Args:
            host: VMware vCenter or ESXi host
            username: VMware username
            password: VMware password
            port: VMware port (default: 443)
            disable_ssl_verification: Whether to disable SSL verification
        """
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.disable_ssl_verification = disable_ssl_verification
        self.service_instance = None
        self.content = None
        self.vm_cache: Dict[str, vim.VirtualMachine] = {}

        self._connect()

    def _connect(self) -> None:
        """Connect to VMware vCenter or ESXi host."""
        try:
            if self.disable_ssl_verification:
                context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
                context.verify_mode = ssl.CERT_NONE
            else:
                context = None

            self.service_instance = connect.SmartConnect(
                host=self.host,
                user=self.username,
                pwd=self.password,
                port=self.port,
                sslContext=context,
            )

            self.content = self.service_instance.RetrieveContent()
            log.info(f"Connected to VMware host {self.host}")
        except Exception as e:
            log.error(f"Failed to connect to VMware host {self.host}: {e}")
            raise

    def _disconnect(self) -> None:
        """Disconnect from VMware vCenter or ESXi host."""
        if self.service_instance:
            connect.Disconnect(self.service_instance)
            log.info(f"Disconnected from VMware host {self.host}")

    def _get_vm_by_name(self, name: str) -> Optional[vim.VirtualMachine]:
        """Get a VM by name.

        Args:
            name: VM name

        Returns:
            VirtualMachine object or None if not found
        """
        # Check cache first
        if name in self.vm_cache:
            return self.vm_cache[name]

        try:
            # Create view of all VMs
            container = self.content.viewManager.CreateContainerView(
                self.content.rootFolder, [vim.VirtualMachine], True
            )

            # Find VM by name
            for vm in container.view:
                if vm.name == name:
                    # Cache the VM
                    self.vm_cache[name] = vm
                    return vm

            log.warning(f"VM with name {name} not found")
            return None
        except Exception as e:
            log.error(f"Error getting VM by name {name}: {e}")
            return None
        finally:
            # Destroy the container view
            if "container" in locals():
                container.Destroy()

    def get_vm_metrics(self, vm_names: List[str], node_names: List[str]) -> List[VMwareMetric]:
        """Get metrics for VMware machines.

        Args:
            vm_names: List of VM names
            node_names: List of node names corresponding to the VMs

        Returns:
            List of VMwareMetric objects
        """
        log.info(f"Getting metrics for VMware machines: {vm_names}")

        if len(vm_names) != len(node_names):
            log.error("VM names and node names must have the same length")
            raise ValueError("VM names and node names must have the same length")

        vm_metrics = []

        for i, vm_name in enumerate(vm_names):
            node_name = node_names[i]

            try:
                vm = self._get_vm_by_name(vm_name)

                if not vm:
                    # Create a metric with unknown status
                    vm_metric = VMwareMetric(
                        name=vm_name,
                        status="disconnected",
                        node_name=node_name,
                    )
                    vm_metrics.append(vm_metric)
                    continue

                # Get VM status
                status = self._get_vm_status(vm)

                # Get VM resource usage
                cpu_usage, memory_usage = self._get_vm_resource_usage(vm)

                # Get VM resource capacity
                cpu_capacity, memory_capacity = self._get_vm_resource_capacity(vm)

                vm_metric = VMwareMetric(
                    name=vm_name,
                    status=status,
                    node_name=node_name,
                    cpu_usage=cpu_usage,
                    memory_usage=memory_usage,
                    cpu_capacity=cpu_capacity,
                    memory_capacity=memory_capacity,
                )

                vm_metrics.append(vm_metric)

            except Exception as e:
                log.error(f"Error getting metrics for VM {vm_name}: {e}")

                # Create a metric with error status
                vm_metric = VMwareMetric(
                    name=vm_name,
                    status="disconnected",
                    node_name=node_name,
                )
                vm_metrics.append(vm_metric)

        return vm_metrics

    def check_vm_alerts(self, vm_metrics: List[VMwareMetric]) -> List[str]:
        """Check for VM alerts based on VM metrics.

        Args:
            vm_metrics: List of VMwareMetric objects

        Returns:
            List of alert messages
        """
        alerts = []

        for vm in vm_metrics:
            # Check for problematic status
            if vm.is_problematic:
                alerts.append(
                    f"VMware machine {vm.name} (node {vm.node_name}) is in {vm.status} state"
                )

                # Check ESXi host status when VM is problematic
                host_status = self._check_esxi_host_status(vm.name)
                if host_status:
                    alerts.append(
                        f"ESXi host for problematic VM {vm.name} (node {vm.node_name}) "
                        f"has status: {host_status}"
                    )

                # Check datastore status when VM is problematic
                datastore_alerts = self._check_datastore_status(vm.name)
                alerts.extend(datastore_alerts)

            # Check for resource issues
            if vm.cpu_percent and vm.cpu_percent > 90:
                alerts.append(
                    f"VMware machine {vm.name} (node {vm.node_name}) has high CPU usage: "
                    f"{vm.cpu_percent:.1f}%"
                )

            if vm.memory_percent and vm.memory_percent > 90:
                alerts.append(
                    f"VMware machine {vm.name} (node {vm.node_name}) has high memory usage: "
                    f"{vm.memory_percent:.1f}%"
                )

        return alerts

    def _check_esxi_host_status(self, vm_name: str) -> Optional[str]:
        """Check the status of the ESXi host running a VM.

        Args:
            vm_name: Name of the VM

        Returns:
            Host status string (green, yellow, red) or None if not available
        """
        try:
            vm = self._get_vm_by_name(vm_name)
            if not vm or not vm.runtime.host:
                return None

            host = vm.runtime.host

            # Check overall host status
            overall_status = host.overallStatus

            # Check for specific alarms on the host
            alarms = host.triggeredAlarmState
            if alarms:
                for alarm in alarms:
                    log.warning(f"ESXi host {host.name} has alarm: {alarm.alarm.info.name}")

            # Check host hardware status
            hardware_status = None
            if hasattr(host, "hardware") and hasattr(host.hardware, "status"):
                hardware_status = host.hardware.status.overallStatus

            # Return the most severe status
            if overall_status == "red" or hardware_status == "red":
                return "red"
            elif overall_status == "yellow" or hardware_status == "yellow":
                return "yellow"
            else:
                return "green"

        except Exception as e:
            log.error(f"Error checking ESXi host status for VM {vm_name}: {e}")
            return None

    def _check_datastore_status(self, vm_name: str) -> List[str]:
        """Check the status of datastores assigned to a VM.

        Args:
            vm_name: Name of the VM

        Returns:
            List of alert messages for problematic datastores
        """
        alerts = []
        try:
            vm = self._get_vm_by_name(vm_name)
            if not vm:
                return alerts

            # Get all datastores used by this VM
            datastores = vm.datastore
            if not datastores:
                return alerts

            for ds in datastores:
                # Check datastore overall status
                if ds.overallStatus != "green":
                    alerts.append(
                        f"Datastore {ds.name} for VM {vm_name} has status: {ds.overallStatus}"
                    )

                # Check datastore alarms
                if hasattr(ds, "triggeredAlarmState") and ds.triggeredAlarmState:
                    for alarm in ds.triggeredAlarmState:
                        alerts.append(
                            f"Datastore {ds.name} for VM {vm_name} has alarm: "
                            f"{alarm.alarm.info.name}"
                        )

                # Check datastore capacity
                if (
                    hasattr(ds, "summary")
                    and hasattr(ds.summary, "capacity")
                    and hasattr(ds.summary, "freeSpace")
                ):
                    capacity = ds.summary.capacity
                    free_space = ds.summary.freeSpace
                    if capacity > 0:
                        free_percent = (free_space / capacity) * 100
                        if free_percent < 10:
                            alerts.append(
                                f"Datastore {ds.name} for VM {vm_name} is low on space: "
                                f"{free_percent:.1f}% free"
                            )

            return alerts
        except Exception as e:
            log.error(f"Error checking datastore status for VM {vm_name}: {e}")
            return alerts

    def _get_vm_status(self, vm: vim.VirtualMachine) -> str:
        """Get the status of a VM.

        Args:
            vm: VirtualMachine object

        Returns:
            VM status string
        """
        power_state = vm.runtime.powerState

        if power_state == vim.VirtualMachinePowerState.poweredOn:
            return "poweredOn"
        elif power_state == vim.VirtualMachinePowerState.poweredOff:
            return "poweredOff"
        elif power_state == vim.VirtualMachinePowerState.suspended:
            return "suspended"
        else:
            return "unknown"

    def _get_vm_resource_usage(self, vm: vim.VirtualMachine) -> tuple:
        """Get the resource usage of a VM.

        Args:
            vm: VirtualMachine object

        Returns:
            Tuple of (cpu_usage, memory_usage)
        """
        try:
            # Get performance metrics
            perf_manager = self.content.perfManager

            # Define metrics to retrieve
            metric_ids = [
                vim.PerformanceManager.MetricId(counterId=6, instance=""),  # CPU usage in MHz
                vim.PerformanceManager.MetricId(counterId=24, instance=""),  # Memory usage in KB
            ]

            # Query for metrics
            spec = vim.PerformanceManager.QuerySpec(
                entity=vm,
                metricId=metric_ids,
                intervalId=20,  # Real-time stats
                maxSample=1,
            )

            result = perf_manager.QueryStats(querySpec=[spec])

            if result and len(result) > 0:
                # Extract CPU and memory usage
                cpu_usage = None
                memory_usage = None

                for metric in result[0].value:
                    if metric.id.counterId == 6:  # CPU usage
                        if metric.value and len(metric.value) > 0:
                            cpu_usage = float(metric.value[0])  # MHz
                    elif metric.id.counterId == 24:  # Memory usage
                        if metric.value and len(metric.value) > 0:
                            memory_usage = float(metric.value[0]) * 1024  # Convert KB to bytes

                return cpu_usage, memory_usage

            return None, None
        except Exception as e:
            log.error(f"Error getting resource usage for VM {vm.name}: {e}")
            return None, None

    def _get_vm_resource_capacity(self, vm: vim.VirtualMachine) -> tuple:
        """Get the resource capacity of a VM.

        Args:
            vm: VirtualMachine object

        Returns:
            Tuple of (cpu_capacity, memory_capacity)
        """
        try:
            # Get CPU capacity in MHz
            cpu_capacity = vm.config.hardware.numCPU * vm.runtime.host.summary.hardware.cpuMhz

            # Get memory capacity in bytes
            memory_capacity = vm.config.hardware.memoryMB * 1024 * 1024  # Convert MB to bytes

            return cpu_capacity, memory_capacity
        except Exception as e:
            log.error(f"Error getting resource capacity for VM {vm.name}: {e}")
            return None, None
