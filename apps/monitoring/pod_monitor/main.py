#!/usr/bin/env python3
"""Pod Monitor main module.

This module serves as the entry point for the Pod Monitor application.
"""

import logging
import signal
import sys
import time
from typing import Optional

import typer
from rich.console import Console
from rich.logging import RichHandler

from .services.kubernetes_service import KubernetesMonitorService
from .services.prometheus_service import PrometheusService
from .services.vmware_service import VMwareMonitorService
from .utils.config import Config, load_config

# Initialize app
app = typer.Typer(help="Kubernetes Pod Monitor")
console = Console()

# Global variables
running = True
kubernetes_service = None
vmware_service = None
prometheus_service = None


def setup_logging(log_level: str = "INFO") -> None:
    """Set up logging configuration.

    Args:
        log_level: Logging level
    """
    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)],
    )


def signal_handler(sig, frame) -> None:
    """Handle signals to gracefully shut down the application.

    Args:
        sig: Signal number
        frame: Current stack frame
    """
    global running
    logging.info("Received shutdown signal, exiting...")
    running = False


@app.command()
def monitor(
    config_path: Optional[str] = typer.Option(
        None, "--config", "-c", help="Path to configuration file"
    ),
    namespace: Optional[str] = typer.Option(
        None, "--namespace", "-n", help="Namespace to monitor (overrides config)"
    ),
    interval: Optional[int] = typer.Option(
        None, "--interval", "-i", help="Monitoring interval in seconds (overrides config)"
    ),
    log_level: str = typer.Option("INFO", "--log-level", "-l", help="Logging level"),
) -> None:
    """Monitor Kubernetes pods, nodes, and VMware machines."""
    # Set up logging
    setup_logging(log_level)
    log = logging.getLogger("pod_monitor")

    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Load configuration
    config = load_config(config_path)

    # Override configuration with command line arguments
    if namespace:
        config.namespaces = [namespace]

    if interval:
        config.monitoring_interval = interval

    log.info(f"Starting pod monitor with interval: {config.monitoring_interval}s")
    log.info(f"Monitoring namespaces: {', '.join(config.namespaces)}")

    # Initialize services
    global kubernetes_service, vmware_service, prometheus_service

    kubernetes_service = KubernetesMonitorService(config.kubeconfig_path)
    kubernetes_service.pod_problematic_threshold = config.pod_problematic_threshold

    # Initialize VMware service if configured
    if config.vmware:
        log.info(f"Initializing VMware service for host: {config.vmware.host}")
        vmware_service = VMwareMonitorService(
            host=config.vmware.host,
            username=config.vmware.username,
            password=config.vmware.password,
            port=config.vmware.port,
            disable_ssl_verification=config.vmware.disable_ssl_verification,
        )

    # Initialize Prometheus service
    prometheus_service = PrometheusService(config.prometheus_port)
    prometheus_service.start_server()

    # Main monitoring loop
    try:
        while running:
            monitor_iteration(config)

            # Sleep until next iteration
            for _ in range(config.monitoring_interval):
                if not running:
                    break
                time.sleep(1)
    except Exception as e:
        log.error(f"Error in monitoring loop: {e}", exc_info=True)
        sys.exit(1)
    finally:
        log.info("Shutting down pod monitor")


def monitor_iteration(config: Config) -> None:
    """Run a single monitoring iteration.

    Args:
        config: Configuration object
    """
    log = logging.getLogger("pod_monitor")

    try:
        # Collect pod metrics for all configured namespaces
        all_pod_metrics = []
        monitored_node_names = set()  # Only track nodes running pods that match our criteria

        # Create label selector string from config if provided
        label_selector = None
        if config.pod_label_selectors:
            label_selector = ",".join([f"{k}={v}" for k, v in config.pod_label_selectors.items()])
            log.info(f"Using label selector: {label_selector}")

        for namespace in config.namespaces:
            try:
                pod_metrics = kubernetes_service.get_pods(namespace, label_selector=label_selector)
                all_pod_metrics.extend(pod_metrics)

                # Collect node names only from pods that match our criteria
                for pod in pod_metrics:
                    if pod.node_name:
                        monitored_node_names.add(pod.node_name)

                # Check for pod alerts
                pod_alerts = kubernetes_service.check_pod_alerts(pod_metrics)
                for alert in pod_alerts:
                    log.warning(f"Pod Alert: {alert}")
                    prometheus_service.record_alert("status", "pod")

                # Update Prometheus metrics for pods
                prometheus_service.update_pod_metrics(pod_metrics)

            except Exception as e:
                log.error(f"Error monitoring namespace {namespace}: {e}")

        # If configured to monitor all nodes, get all nodes in the cluster
        node_names_to_monitor = list(monitored_node_names)
        if config.monitor_all_nodes:
            log.info("Configured to monitor all nodes in the cluster")
            # Get all nodes in the cluster
            all_nodes = kubernetes_service.get_all_nodes()
            node_names_to_monitor = [node.name for node in all_nodes]
        else:
            log.info(f"Monitoring only nodes running selected pods: {node_names_to_monitor}")

        # Collect node metrics only for nodes we're monitoring
        if node_names_to_monitor:
            node_metrics = kubernetes_service.get_nodes(node_names_to_monitor)

            # Check for node alerts
            node_alerts = kubernetes_service.check_node_alerts(node_metrics)
            for alert in node_alerts:
                log.warning(f"Node Alert: {alert}")
                prometheus_service.record_alert("status", "node")

            # Update Prometheus metrics for nodes
            prometheus_service.update_node_metrics(node_metrics)

            # Collect VMware metrics if VMware service is configured
            if vmware_service:
                # Get VMware machine names from node metrics
                vm_names = []
                node_names = []

                for node in node_metrics:
                    if node.vmware_machine_name:
                        vm_names.append(node.vmware_machine_name)
                        node_names.append(node.name)

                if vm_names:
                    try:
                        # Get VMware metrics
                        vmware_metrics = vmware_service.get_vm_metrics(vm_names, node_names)

                        # Check for VMware alerts
                        vm_alerts = vmware_service.check_vm_alerts(vmware_metrics)
                        for alert in vm_alerts:
                            log.warning(f"VMware Alert: {alert}")
                            prometheus_service.record_alert("status", "vmware")

                        # Update Prometheus metrics for VMware machines
                        prometheus_service.update_vmware_metrics(vmware_metrics)

                    except Exception as e:
                        log.error(f"Error monitoring VMware machines: {e}")
        else:
            log.info("No nodes to monitor based on current configuration")

    except Exception as e:
        log.error(f"Error in monitoring iteration: {e}", exc_info=True)


if __name__ == "__main__":
    app()
