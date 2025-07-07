FROM ollama/ollama:0.9.5

# Set working directory
WORKDIR /app

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies including NVIDIA components and GPU check requirements
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    curl \
    git \
    python3 \
    python3-dev \
    python3-pip \
    python3-setuptools && \
    rm -rf /var/lib/apt/lists/* && \
    pip3 install --no-cache-dir nvidia-ml-py3

# Copy startup scripts into the image
COPY ollama-startup.sh /app/scripts/ollama-startup.sh
COPY check-gpu.sh /app/scripts/check-gpu.sh
RUN chmod +x /app/scripts/*.sh

# Set default environment variables
ENV OLLAMA_HOST=0.0.0.0
ENV OLLAMA_ORIGINS=*

# Create user for running ollama
RUN groupadd -g 1000 ollama && \
    useradd -u 1000 -g 1000 -m -s /bin/bash ollama

# Expose the default port
EXPOSE 11434

# Set the entrypoint to the startup script
# This script will check for GPU availability and start the Ollama service
ENTRYPOINT ["/app/scripts/ollama-startup.sh"]
