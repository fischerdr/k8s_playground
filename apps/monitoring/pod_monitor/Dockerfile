FROM fedora:latest

LABEL maintainer="K8s Playground Team"
LABEL description="Kubernetes Pod Monitor for monitoring pod states and VMware integration"

# Install dependencies
RUN dnf update -y && \
    dnf install -y python3 python3-pip python3-devel gcc && \
    dnf clean all && \
    rm -rf /var/cache/dnf

# Create non-root user
RUN useradd -m -s /bin/bash -u 1000 podmonitor

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt && \
    # Remove build dependencies to reduce image size
    dnf remove -y gcc python3-devel && \
    dnf clean all && \
    rm -rf /var/cache/dnf

# Copy application code
COPY . .

# Set ownership to non-root user
RUN chown -R podmonitor:podmonitor /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PORT=9090

# Create directory for temporary files with proper permissions
RUN mkdir -p /app/tmp && \
    chown -R podmonitor:podmonitor /app/tmp && \
    chmod 755 /app/tmp

# Switch to non-root user
USER podmonitor

# Expose port for metrics and health endpoints
EXPOSE 9090

# Set health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:9090/health || exit 1

# Run the application
ENTRYPOINT ["python3", "-m", "pod_monitor.main"]
CMD ["monitor"]
