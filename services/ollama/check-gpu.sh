#!/bin/bash

echo "Verifying GPU capabilities inside container..."

# Check if nvidia-smi is available and working
if command -v nvidia-smi &>/dev/null; then
    echo "✓ nvidia-smi found in container"

    # Query GPU info to confirm it's working
    if nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv 2>/dev/null; then
        echo "✓ GPU verification passed!"
        exit 0
    else
        echo "✗ GPU query failed"
        exit 1
    fi
else
    echo "✗ nvidia-smi not available in container"
    echo "ERROR: GPU acceleration required but not detected!"
    exit 1
fi
