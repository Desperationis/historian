#!/usr/bin/env bash
set -euo pipefail

SRC_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SRC_DIR"

# --- Must NOT be root ---
if [ "$(id -u)" -eq 0 ]; then
    echo "Error: do NOT run with sudo. Run as: bash install_requirements.bash" >&2
    echo "The script will ask for sudo only when needed." >&2
    exit 1
fi

echo "=== historian — Installing system and Python dependencies ==="

# --- System packages (Debian/Ubuntu) ---
echo ""
echo "[1/4] Installing system packages via apt..."
sudo apt-get update -qq
sudo apt-get install -y \
    python3 \
    ffmpeg \
    exiftool \
    curl

# --- uv ---
echo ""
echo "[2/4] Checking uv..."
if ! command -v uv &>/dev/null && [ ! -x "$HOME/.local/bin/uv" ]; then
    echo "  Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
fi
# Resolve uv path
if command -v uv &>/dev/null; then
    UV_BIN="$(command -v uv)"
else
    UV_BIN="$HOME/.local/bin/uv"
fi

# --- Python dependencies ---
echo ""
echo "[3/4] Installing Python dependencies via uv..."
"$UV_BIN" sync

# --- aider ---
echo ""
echo "[4/4] Installing aider..."
if ! command -v aider &>/dev/null; then
    "$UV_BIN" tool install aider-chat
else
    echo "  aider already installed."
fi

# --- Ollama model (optional) ---
if command -v ollama &>/dev/null; then
    echo ""
    echo "Ollama detected. Pulling dolphin-llama3 model..."
    ollama pull dolphin-llama3 || echo "Warning: could not pull dolphin-llama3. Run 'ollama pull dolphin-llama3' manually."
else
    echo ""
    echo "NOTE: ollama is not installed. historian requires ollama with the dolphin-llama3 model."
    echo "Install ollama from https://ollama.com/download, then run: ollama pull dolphin-llama3"
fi

# --- Verify ---
echo ""
echo "=== Verification ==="
echo -n "Python:   "; "$UV_BIN" run python --version
echo -n "ffmpeg:   "; ffmpeg -version 2>&1 | head -1 || echo "NOT FOUND"
echo -n "exiftool: "; exiftool -ver 2>/dev/null || echo "NOT FOUND"
echo -n "aider:    "; command -v aider &>/dev/null && echo "OK" || echo "NOT FOUND"
echo -n "ollama:   "; command -v ollama &>/dev/null && echo "OK" || echo "NOT INSTALLED (required)"

echo ""
echo "=== Done! ==="
echo "Run from source with:  $UV_BIN run historian sort <source> <dest>"
echo "                       $UV_BIN run historian compress <folder>"
echo "Run tests with:        $UV_BIN run pytest"
