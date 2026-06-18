#!/usr/bin/env bash
# Launch the Bangladesh Weather Dashboard on macOS.
# Creates a .venv if needed, installs dependencies, and opens Streamlit.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VENV_DIR="$SCRIPT_DIR/.venv"
PYTHON="python3"
PORT=8501

echo "🌦️  Bangladesh Weather Dashboard"
echo "================================="

# Check Python
if ! command -v "$PYTHON" &>/dev/null; then
    echo "❌  Python 3 not found. Install from https://www.python.org or via Homebrew:"
    echo "    brew install python3"
    exit 1
fi

PYTHON_VERSION=$("$PYTHON" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "✅  Python $PYTHON_VERSION detected"

# Create venv if missing
if [ ! -d "$VENV_DIR" ]; then
    echo "🔧  Creating virtual environment…"
    "$PYTHON" -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"
echo "✅  Virtual environment active"

# Install / update dependencies
echo "📦  Installing dependencies…"
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo ""
echo "🚀  Starting app at http://localhost:$PORT"
echo "    Press Ctrl+C to stop."
echo ""

# Open browser after a short delay (Streamlit opens automatically, but this is a fallback)
(sleep 2 && open "http://localhost:$PORT") &

streamlit run src/app.py \
    --server.port "$PORT" \
    --server.headless false \
    --browser.gatherUsageStats false
