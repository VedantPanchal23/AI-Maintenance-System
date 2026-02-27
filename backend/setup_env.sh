#!/bin/bash
# ============================================================
#  AI Predictive Maintenance System — Virtual Environment Setup
#  Target: Python 3.11+ with RTX 3050 6GB GPU (CUDA 12.x)
# ============================================================

set -e

echo ""
echo "==================================================="
echo " AI Predictive Maintenance - Environment Setup"
echo " GPU Target: NVIDIA RTX 3050 6GB (CUDA 12.x)"
echo "==================================================="
echo ""

# --- Step 1: Find Python 3.11+ ---
echo "[1/6] Locating Python 3.11+..."

if command -v python3.11 &> /dev/null; then
    PYTHON_CMD=python3.11
elif command -v python3.12 &> /dev/null; then
    PYTHON_CMD=python3.12
elif command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
else
    echo "[ERROR] Python 3.11+ not found."
    exit 1
fi

echo "  Found: $PYTHON_CMD"
$PYTHON_CMD --version

# --- Step 2: Create virtual environment ---
echo ""
echo "[2/6] Creating virtual environment..."
if [ -d "venv" ]; then
    echo "  Removing existing venv..."
    rm -rf venv
fi
$PYTHON_CMD -m venv venv
echo "  venv created."

# --- Step 3: Activate and upgrade pip ---
echo ""
echo "[3/6] Activating venv and upgrading pip..."
source venv/bin/activate
pip install --upgrade pip setuptools wheel

# --- Step 4: Install PyTorch with CUDA ---
echo ""
echo "[4/6] Installing PyTorch with CUDA 12.1 support..."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# --- Step 5: Install dependencies ---
echo ""
echo "[5/6] Installing project dependencies..."
pip install -r requirements.txt

# --- Step 6: Verify ---
echo ""
echo "[6/6] Verifying installation..."
python -c "
import torch
print(f'  PyTorch: {torch.__version__}')
print(f'  CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'  GPU: {torch.cuda.get_device_name(0)}')
    print(f'  GPU Memory: {torch.cuda.get_device_properties(0).total_mem / 1024**3:.1f} GB')
"

echo ""
echo "Setup complete! Activate with: source venv/bin/activate"
