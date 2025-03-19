#!/usr/bin/env python3
"""Pod Monitor main module.

This module serves as the entry point for the Pod Monitor application.
"""

import logging
import signal
import sys
import threading
import time
from typing import Optional

import typer
import uvicorn
from fastapi import FastAPI, Response
from rich.console import Console
from rich.logging import RichHandler

from .services.kubernetes_service import KubernetesMonitorService
from .services.prometheus_service import PrometheusService
from .services.vmware_service import VMwareMonitorService
from .utils.config import Config, load_config

# Initialize app
app = typer.Typer(help="Kubernetes Pod Monitor")
console = Console()

# Initialize FastAPI app for health checks and metrics
api_app = FastAPI(title="Pod Monitor API")

# Global variables
running = True
kubernetes_service = None
vmware_service = None
prometheus_service = None
health_status = {"status": "starting"}


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
    """Monitor Kubernetes pods, nodes, and VMware machines.

    Args:
        config_path: Path to configuration file
        namespace: Namespace to monitor (overrides config)
        interval: Monitoring interval in seconds (overrides config)
        log_level: Logging level
    """
    global kubernetes_service, vmware_service, prometheus_service, health_status

    # Set up logging
    setup_logging(log_level)
    log = logging.getLogger(__name__)

    # Set up signal handler
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start API server in a separate thread
    api_thread = threading.Thread(target=start_api_server, daemon=True)
    api_thread.start()
    log.info("API server started on port 9090")

    try:
        # Load configuration
        config = load_config(config_path)
        log.info(f"Configuration loaded: {config}")

        # Override configuration with command-line arguments
        if namespace:
            config.namespaces = [namespace]
        if interval:
            config.monitoring_interval = interval

        # Initialize services
        kubernetes_service = KubernetesMonitorService(config.kubeconfig_path)
        prometheus_service = PrometheusService()

        # Update health status
        health_status = {"status": "initializing"}

        # Initialize VMware service if configured
        if config.vmware and config.vmware.host:
            vmware_service = VMwareMonitorService(
                host=config.vmware.host,
                username=config.vmware.username,
                password=config.vmware.password,
                port=config.vmware.port,
                disable_ssl_verification=config.vmware.disable_ssl_verification,
            )

        # Update health status
        health_status = {"status": "ok"}

        log.info(f"Starting monitoring with interval: {config.monitoring_interval}s")

        # Main monitoring loop
        while running:
            try:
                monitor_iteration(config)
            except Exception as e:
                log.error(f"Error in monitoring iteration: {e}", exc_info=True)
                health_status = {"status": "degraded", "error": str(e)}

            time.sleep(config.monitoring_interval)

    except Exception as e:
        log.error(f"Error in monitor: {e}", exc_info=True)
        health_status = {"status": "error", "error": str(e)}
        sys.exit(1)


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


@api_app.get("/health")
def health() -> Response:
    global health_status
    if kubernetes_service and prometheus_service:
        health_status = {"status": "ok"}
    else:
        health_status = {"status": "unhealthy"}
    return Response(content="ok", status_code=200)


@api_app.get("/metrics")
def metrics():
    # This endpoint will be handled by the Prometheus client
    pass


def start_api_server() -> None:
    # Mount Prometheus metrics
    if prometheus_service:
        metrics_app = prometheus_service.get_app()
        api_app.mount("/metrics", metrics_app)

    # Start the API server
    uvicorn.run(api_app, host="0.0.0.0", port=9090)


if __name__ == "__main__":
    app()
