#!/usr/bin/env bash
set -euo pipefail

echo "=== historian — Installing system and Python dependencies ==="

# --- System packages (Debian/Ubuntu) ---
echo ""
echo "[1/4] Installing system packages via apt..."
sudo apt-get update -qq
sudo apt-get install -y \
    python3 \
    exiftool

# --- uv ---
echo ""
echo "[2/4] Checking uv..."
if ! command -v uv &>/dev/null && [ ! -x "$HOME/.local/bin/uv" ]; then
    echo "  Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
fi

# --- Python dependencies ---
echo ""
echo "[3/4] Installing Python dependencies via uv..."
uv sync

# --- aider ---
echo ""
echo "[4/4] Installing aider..."
if ! command -v aider &>/dev/null; then
    uv tool install aider-chat
else
    echo "  aider already installed."
fi

# --- Ollama model (optional) ---
if command -v ollama &>/dev/null; then
    echo ""
    echo "Ollama detected. Pulling dolphin-llama3 model..."
    ollama pull dolphin-llama3
else
    echo ""
    echo "NOTE: ollama is not installed. historian requires ollama with the dolphin-llama3 model."
    echo "Install ollama from https://ollama.com/download, then run: ollama pull dolphin-llama3"
fi

# --- Verify ---
echo ""
echo "=== Verification ==="
echo -n "Python:   "; uv run python --version
echo -n "exiftool: "; exiftool -ver 2>/dev/null || echo "NOT FOUND"
echo -n "aider:    "; command -v aider &>/dev/null && echo "OK" || echo "NOT FOUND"
echo -n "ollama:   "; command -v ollama &>/dev/null && echo "OK" || echo "NOT INSTALLED (required)"

echo ""
echo "=== Done! ==="
echo "Run from source with:  uv run historian <source> <dest>"
echo "Run tests with:        uv run pytest"
