#!/usr/bin/env bash

# Post-create actions for the devcontainer: install `uv` and build project dependencies
# This script is idempotent: it will skip steps if `uv` is already available.
# Enhanced with step-by-step status updates and error handling.

set -euo pipefail

echo "[post_create] Starting devcontainer post-create script"

# Step 1: Check if 'uv' is already installed
if command -v uv >/dev/null 2>&1; then
	echo "[post_create] 'uv' is already installed. Skipping installation."
else
	echo "[post_create] Installing 'uv'..."
	if ! curl -LsSf https://astral.sh/uv/install.sh | sh; then
		echo "[post_create] ERROR: Failed to install 'uv'. Exiting." >&2
		exit 1
	fi
	echo "[post_create] 'uv' installation complete."
fi

# Step 2: Activate virtual environment
if [ -d ".venv" ] && [ -f ".venv/bin/activate" ]; then
	echo "[post_create] Activating Python virtual environment..."
	source .venv/bin/activate
	echo "[post_create] Virtual environment activated."
else
	echo "[post_create] ERROR: .venv not found or missing activate script. Exiting." >&2
	exit 1
fi

# Step 3: Sync project dependencies using 'uv'
echo "[post_create] Syncing project dependencies with 'uv'..."
if uv run sync; then
	echo "[post_create] Dependency sync complete."
else
	echo "[post_create] ERROR: 'uv run sync' failed. Exiting." >&2
	exit 1
fi

echo "[post_create] Devcontainer post-create steps finished successfully."