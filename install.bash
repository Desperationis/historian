#!/usr/bin/env bash
set -euo pipefail

INSTALL_DIR="/opt/historian"
BIN_LINK="/usr/local/bin/historian"

echo "=== historian — Build & Install ==="

# --- Must NOT be root ---
if [ "$(id -u)" -eq 0 ]; then
    echo "Error: do NOT run with sudo. Run as: bash install.bash" >&2
    echo "The script will ask for sudo only when needed." >&2
    exit 1
fi

SRC_DIR="$(cd "$(dirname "$0")" && pwd)"

# --- 1. Nuke previous install ---
echo "[1/6] Removing previous install..."
sudo rm -rf "$INSTALL_DIR"
sudo rm -f "$BIN_LINK"

# --- 2. Clean source tree ---
echo "[2/6] Cleaning source tree..."
find "$SRC_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$SRC_DIR" -type f -name "*.pyc" -delete 2>/dev/null || true
find "$SRC_DIR" -type f -name "*.pyo" -delete 2>/dev/null || true
rm -rf "$SRC_DIR/.venv"
find "$SRC_DIR" -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
rm -rf "$SRC_DIR/dist" "$SRC_DIR/build"

# --- 3. System dependencies ---
echo "[3/6] Installing system packages..."
sudo apt-get update -qq
sudo apt-get install -y -qq python3 exiftool > /dev/null

# --- 4. Install uv if missing ---
echo "[4/6] Checking uv..."
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

# --- 5. Copy clean source & build fresh venv ---
echo "[5/6] Building fresh from source..."
sudo mkdir -p "$INSTALL_DIR"
sudo cp -a "$SRC_DIR/." "$INSTALL_DIR/"
# Clean artifacts from the copy
sudo find "$INSTALL_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
sudo find "$INSTALL_DIR" -type f -name "*.pyc" -delete 2>/dev/null || true
sudo find "$INSTALL_DIR" -type f -name "*.pyo" -delete 2>/dev/null || true
sudo rm -rf "$INSTALL_DIR/.venv"
sudo rm -rf "$INSTALL_DIR/.git"
# Own the install dir as the current user so uv runs without issues
sudo chown -R "$(id -u):$(id -g)" "$INSTALL_DIR"

# Build a completely fresh venv
cd "$INSTALL_DIR"
"$UV_BIN" sync --reinstall

# Make the install dir world-readable so sudo can use it too
chmod -R a+rX "$INSTALL_DIR"

# --- 6. Install global launcher ---
echo "[6/6] Installing launcher..."

sudo tee "$BIN_LINK" > /dev/null <<LAUNCHER
#!/usr/bin/env bash
cd $INSTALL_DIR && exec "$UV_BIN" run historian "\$@"
LAUNCHER
sudo chmod +x "$BIN_LINK"

# --- Ollama model check ---
if command -v ollama &>/dev/null; then
    echo ""
    echo "Ollama detected. Pulling dolphin-llama3 model..."
    ollama pull dolphin-llama3
else
    echo ""
    echo "NOTE: ollama is not installed. historian requires ollama with the dolphin-llama3 model."
    echo "Install ollama from https://ollama.com/download, then run: ollama pull dolphin-llama3"
fi

echo ""
echo "=== Installed ==="
echo "  Location:  $INSTALL_DIR (owned by $USER)"
echo "  Launcher:  $BIN_LINK"
echo "  Run:       historian <source> <dest>"
echo "  Sudo:      sudo historian <source> <dest>"
