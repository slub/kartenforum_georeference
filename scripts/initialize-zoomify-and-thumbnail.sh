#!/bin/bash

######################################################################
# Author      : Pouria Rezaei (pouria.rezaei@pikobytes.de)
# File        : initialize-zoomify-and-thumbnail.sh
# Created     : August 30, 2024
#
# Description : Utility script to initialize thumbnails and Zoomify
#               tiles for test data.
#
# Usage       : ./initialize-zoomify-and-thumbnail.sh
######################################################################

# Define the paths to the Python scripts
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
INITIALIZE_THUMBNAILS="$SCRIPT_DIR/initialize_thumbnails.py"
INITIALIZE_ZOOMIFY_TILES="$SCRIPT_DIR/initialize_zoomify_tiles.py"

# Set the PYTHONPATH to include the project root directory
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

# Ensure the virtual environment is activated before running scripts
VENV_PATH="$PROJECT_ROOT/.venv/bin/python"
if [[ ! -f "$VENV_PATH" ]]; then
    echo "Error: Virtual environment not found at $VENV_PATH"
    exit 1
fi

# Run the Python scripts
run_script() {
    local script_name=$1
    echo "Starting $script_name initialization..."
    "$VENV_PATH" "$script_name" || {
        echo "Error: Failed to run $script_name"
        exit 1
    }
}

run_script "$INITIALIZE_THUMBNAILS"
run_script "$INITIALIZE_ZOOMIFY_TILES"

echo "Initialization complete."
