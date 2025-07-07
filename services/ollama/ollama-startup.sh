#!/bin/bash
set -e

# Fix permissions for .ollama directory
echo "Setting up .ollama directory permissions..."
mkdir -p /home/ollama/.ollama
chown -R 1000:1000 /home/ollama/.ollama
chmod -R 755 /home/ollama/.ollama

# Run GPU check first
echo "Running GPU verification before starting Ollama..."
if [ -f "/app/scripts/check-gpu.sh" ]; then
    if ! sh /app/scripts/check-gpu.sh; then
        echo "ERROR: GPU check failed! Cannot start Ollama without proper GPU support."
        exit 1
    fi
    echo "GPU check passed successfully!"
else
    echo "Warning: GPU check script not found, proceeding without GPU verification..."
fi

echo "Starting Ollama server as a managed process..."

# Create log directory
mkdir -p /var/log/ollama
chown ollama:ollama /var/log/ollama

# Create a wrapper script for better process management
cat >/tmp/ollama-wrapper.sh <<'EOF'
#!/bin/bash
cd /home/ollama
export HOME=/home/ollama
export PATH=/usr/local/bin:/usr/bin:/bin
exec ollama serve >> /var/log/ollama/ollama.log 2>&1
EOF

chmod +x /tmp/ollama-wrapper.sh

# Start Ollama in background with proper process management
echo "Launching Ollama server (logs: /var/log/ollama/ollama.log)..."
su ollama -c "/tmp/ollama-wrapper.sh" &
OLLAMA_PID=$!

# Wait for Ollama to be ready with timeout
echo "Waiting for Ollama service to start..."
for i in {1..30}; do
    if curl -f http://localhost:11434/api/version >/dev/null 2>&1; then
        echo "Ollama service is ready!"
        break
    fi

    echo "Waiting... ($i/30)"
    sleep 2
done

# Check if Ollama process is still running
if ! kill -0 $OLLAMA_PID 2>/dev/null; then
    echo "ERROR: Ollama process failed to start properly"
    exit 1
fi

echo "Ollama server started successfully (PID: $OLLAMA_PID)"

# Download models if specified
if [ ! -z "$OLLAMA_PREDOWNLOAD_MODELS" ]; then
    echo "Downloading models: $OLLAMA_PREDOWNLOAD_MODELS"
    IFS=',' read -ra MODELS <<<"$OLLAMA_PREDOWNLOAD_MODELS"
    for model in "${MODELS[@]}"; do
        model=$(echo "$model" | xargs) # trim whitespace
        echo "Pulling model: $model"
        if ! su ollama -c "ollama pull \"$model\""; then
            echo "Warning: Failed to pull model $model"
        fi
    done

    echo "Model download process completed"
fi

echo "Ollama startup complete, keeping server running..."
echo "Monitor logs with: tail -f /var/log/ollama/ollama.log"
# Monitor the Ollama process and restart if it dies
while true; do
    if ! kill -0 $OLLAMA_PID 2>/dev/null; then
        echo "$(date): Ollama process died, attempting restart..." | tee -a /var/log/ollama/restart.log
        su ollama -c "/tmp/ollama-wrapper.sh" &
        OLLAMA_PID=$!
        echo "$(date): Restarted Ollama (new PID: $OLLAMA_PID)" | tee -a /var/log/ollama/restart.log

        # Wait a bit for the new process to stabilize
        sleep 5
    fi

    sleep 30
done
