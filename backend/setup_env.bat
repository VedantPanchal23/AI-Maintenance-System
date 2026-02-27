@echo off
REM ============================================================
REM  AI Predictive Maintenance System — Virtual Environment Setup
REM  Target: Python 3.11+ with RTX 3050 6GB GPU (CUDA 12.x)
REM ============================================================

echo.
echo ===================================================
echo  AI Predictive Maintenance - Environment Setup
echo  GPU Target: NVIDIA RTX 3050 6GB (CUDA 12.x)
echo ===================================================
echo.

REM --- Step 1: Find Python 3.11 ---
echo [1/6] Locating Python 3.11...

REM Try common Python 3.11 locations
where python3.11 >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set PYTHON_CMD=python3.11
    goto :found_python
)

REM Try py launcher (Windows Python Launcher)
py -3.11 --version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set PYTHON_CMD=py -3.11
    goto :found_python
)

REM Try plain python and check version
python --version 2>&1 | findstr "3.11 3.12" >nul
if %ERRORLEVEL% EQU 0 (
    set PYTHON_CMD=python
    goto :found_python
)

echo [ERROR] Python 3.11+ not found.
echo Please install Python 3.11 from https://www.python.org/downloads/
echo Or use: py -3.11 if you have multiple versions via py launcher.
pause
exit /b 1

:found_python
echo   Found: %PYTHON_CMD%
%PYTHON_CMD% --version

REM --- Step 2: Create virtual environment ---
echo.
echo [2/6] Creating virtual environment...
if exist venv (
    echo   Existing venv found. Removing...
    rmdir /s /q venv
)
%PYTHON_CMD% -m venv venv
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to create virtual environment.
    pause
    exit /b 1
)
echo   venv created successfully.

REM --- Step 3: Activate and upgrade pip ---
echo.
echo [3/6] Activating venv and upgrading pip...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip setuptools wheel

REM --- Step 4: Install PyTorch with CUDA 12.1 (for RTX 3050) ---
echo.
echo [4/6] Installing PyTorch with CUDA 12.1 support (RTX 3050)...
echo   This may take several minutes...
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

REM Verify CUDA
python -c "import torch; print(f'  PyTorch {torch.__version__}'); print(f'  CUDA available: {torch.cuda.is_available()}'); print(f'  GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"N/A\"}')"

REM --- Step 5: Install all project dependencies ---
echo.
echo [5/6] Installing project dependencies...
pip install -r requirements.txt

REM --- Step 6: Verify installation ---
echo.
echo [6/6] Verifying installation...
python -c "
import sys
print(f'  Python: {sys.version}')

import torch
print(f'  PyTorch: {torch.__version__}')
print(f'  CUDA: {torch.version.cuda}')
print(f'  cuDNN: {torch.backends.cudnn.version()}')
print(f'  GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"Not detected\"}')
gpu_mem = torch.cuda.get_device_properties(0).total_mem / 1024**3 if torch.cuda.is_available() else 0
print(f'  GPU Memory: {gpu_mem:.1f} GB')

import sklearn; print(f'  scikit-learn: {sklearn.__version__}')
import xgboost; print(f'  XGBoost: {xgboost.__version__}')
import lightgbm; print(f'  LightGBM: {lightgbm.__version__}')
import fastapi; print(f'  FastAPI: {fastapi.__version__}')
import pandas; print(f'  Pandas: {pandas.__version__}')
import numpy; print(f'  NumPy: {numpy.__version__}')
print()
print('  All dependencies installed successfully!')
"

echo.
echo ===================================================
echo  Setup Complete!
echo  
echo  To activate the environment:
echo    venv\Scripts\activate
echo  
echo  To train models (GPU-accelerated):
echo    python -m scripts.train_models
echo  
echo  To start the API server:
echo    uvicorn app.main:app --reload
echo ===================================================
echo.
pause
