FROM fedora:latest

LABEL maintainer="K8s Playground Team"
LABEL description="Kubernetes Pod Monitor for monitoring pod states and VMware integration"

# Install dependencies
RUN dnf update -y && \
    dnf install -y python3 python3-pip && \
    dnf clean all

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

# Expose port for metrics
EXPOSE 9090

# Run the application
ENTRYPOINT ["python3", "-m", "pod_monitor.main"]
CMD ["monitor"]
