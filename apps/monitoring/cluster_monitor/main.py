#!/usr/bin/env python3
"""Kubernetes Cluster Monitor main module.

This module serves as the entry point for the Kubernetes Cluster Monitor application.
"""

import logging
import sys
from typing import Dict, List, Optional

import typer
from rich.console import Console
from rich.logging import RichHandler

from .models.cluster import ClusterMetrics
from .services.monitor import ClusterMonitorService
from .utils.config import load_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)],
)
log = logging.getLogger("cluster_monitor")
console = Console()

app = typer.Typer(help="Kubernetes Cluster Monitor")


@app.command()
def monitor(
    namespace: Optional[str] = typer.Option(None, "--namespace", "-n", help="Namespace to monitor"),
    interval: int = typer.Option(60, "--interval", "-i", help="Monitoring interval in seconds"),
    output: str = typer.Option(
        "console", "--output", "-o", help="Output format (console, json, prometheus)"
    ),
) -> None:
    """Monitor Kubernetes cluster resources and health."""
    log.info(f"Starting cluster monitoring with interval: {interval}s")

    config = load_config()
    monitor_service = ClusterMonitorService(config)

    try:
        metrics = monitor_service.collect_metrics(namespace)
        _display_metrics(metrics, output)
    except Exception as e:
        log.error(f"Error monitoring cluster: {e}")
        sys.exit(1)


def _display_metrics(metrics: ClusterMetrics, output_format: str) -> None:
    """Display collected metrics in the specified format.

    Args:
        metrics: The collected cluster metrics
        output_format: Format to display metrics (console, json, prometheus)
    """
    if output_format == "console":
        console.print("[bold green]Cluster Metrics:[/bold green]")
        console.print(metrics)
    elif output_format == "json":
        console.print_json(metrics.to_dict())
    elif output_format == "prometheus":
        for metric in metrics.to_prometheus():
            console.print(metric)
    else:
        log.warning(f"Unknown output format: {output_format}")


if __name__ == "__main__":
    app()
