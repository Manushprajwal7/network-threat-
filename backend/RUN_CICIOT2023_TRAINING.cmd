@echo off
REM Quick reference for CICIoT2023 training workflow
REM Run this from the backend directory

echo.
echo ====================================================================
echo CICIoT2023 Model Training Workflow
echo ====================================================================
echo.

REM Get current directory
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo Current directory: %cd%
echo.

REM Step 1: Optional cleanup
echo [STEP 1] Cleaning up old CICIDS2017 artifacts...
echo.
echo Run this command:
echo   python ml_model/cleanup_cicids2017.py
echo.
echo (This is optional - removes old .pkl files and reports)
echo.

REM Step 2: Install dependencies
echo [STEP 2] Installing dependencies...
echo.
echo Run this command:
echo   pip install -r requirements.txt
echo.
echo (xgboost is already in requirements.txt)
echo.

REM Step 3: Train models
echo [STEP 3] Training CICIoT2023 models...
echo.
echo For NORMAL TRAINING (full training on all data):
echo   python ml_model/train_ciciot2023_models.py
echo.
echo For FAST TRAINING (subsample SVM/KNN to 15-20k rows):
echo   python ml_model/train_ciciot2023_models.py --fast
echo.
echo Expected output:
echo   - Loads train/, validation/, test/ folders from CICIoT2023 dataset
echo   - Trains 7 models: RF, DT, LR, SVM, KNN, XGB, NB
echo   - Saves models to: ml_model/saved_models/*.pkl
echo   - Generates reports to: ml_model/reports/model_comparison_ciciot2023.csv
echo.
echo Training typically takes 10-30 minutes depending on dataset size.
echo.

REM Step 4: Start API
echo [STEP 4] Starting API server...
echo.
echo Run this command:
echo   python api/app.py
echo.
echo The API will:
echo   - Load all 7 trained CICIoT2023 models
echo   - Serve predictions at http://localhost:5000/api/predict
echo   - Serve reports at http://localhost:5000/api/research/*
echo.

REM Step 5: View results
echo [STEP 5] View results in frontend
echo.
echo Navigate to:
echo   http://localhost:3000/results
echo.
echo The Results page will automatically:
echo   - Detect CICIoT2023 dataset (by reading report files)
echo   - Display all 7 model metrics
echo   - Show confusion matrices and per-class results
echo   - Provide CSV exports
echo.

echo.
echo ====================================================================
echo COMPLETE WORKFLOW (copy-paste these commands in order):
echo ====================================================================
echo.
echo Step 1 (Optional - cleanup old files):
echo   python ml_model/cleanup_cicids2017.py
echo.
echo Step 2 (Install packages):
echo   pip install -r requirements.txt
echo.
echo Step 3a (Train models - NORMAL):
echo   python ml_model/train_ciciot2023_models.py
echo.
echo Step 3b (Train models - FAST):
echo   python ml_model/train_ciciot2023_models.py --fast
echo.
echo Step 4 (Start API):
echo   python api/app.py
echo.
echo Then open browser to http://localhost:3000/results
echo.
echo ====================================================================
echo.

pause
