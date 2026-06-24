# CICIoT2023 Dataset Migration Guide

## Overview
This document describes the complete migration from CICIDS2017 to CICIoT2023 dataset for the ML backend.

## Key Changes

### 1. New Dataset Structure
- **CICIoT2023 location**: `C:\Users\Manus\OneDrive\Desktop\L-thirupathi\dataset\archive (3)\CICIOT23`
- **Folder structure**:
  ```
  CICIOT23/
  ├── train/     (training CSV files)
  ├── test/      (test CSV files)
  └── validation/ (validation CSV files)
  ```
- **Key difference**: No random train/test split. Each folder is used as-is.

### 2. New Scripts Created

#### `preprocess_ciciot2023.py`
- Loads CSV files from train/, validation/, test/ folders separately
- Auto-detects label column (handles "label", "Label", "Attack", "class", etc.)
- Cleans column names and handles NaN/Infinity values
- Class-aware deduplication (dedups BENIGN, keeps all attacks)
- Applies outlier clipping and scaling
- Saves: scaler.pkl, label_encoder.pkl, feature_columns.pkl, clip_lower.pkl, clip_upper.pkl

#### `train_ciciot2023_models.py`
Trains all 7 models:
1. **Random Forest** - 200 estimators, max_depth=20
2. **Decision Tree** - max_depth=15
3. **Logistic Regression** - C=0.5
4. **SVM** - RBF kernel with calibration
5. **KNN** - k=7
6. **XGBoost** - 150 estimators, max_depth=6
7. **Naive Bayes** - Gaussian

**Reports generated**:
- `model_comparison_ciciot2023.csv` - Model metrics comparison
- `classification_report_ciciot2023.txt` - Detailed per-class metrics
- `confusion_matrix_ciciot2023.png` - Confusion matrix visualization
- `per_class_metrics_ciciot2023.csv` - Per-class precision/recall/f1
- `latency_report_ciciot2023.csv` - Training and prediction times
- `research_summary_ciciot2023.txt` - Summary text report

#### `cleanup_cicids2017.py`
Removes all old CICIDS2017 artifacts:
- All .pkl files from saved_models/
- All report files from reports/

### 3. Updated Scripts

#### `research_api.py`
- **Dataset detection**: Automatically detects if CICIoT2023 (by presence of `model_comparison_ciciot2023.csv`)
- **Dataset-agnostic endpoints**: All endpoints work with both datasets
- **Updated report filenames**: Endpoints try CICIoT2023 files first, fall back to CICIDS2017
- **Metadata**: Shows correct num_features, num_classes, split_mode based on dataset

#### `predict.py`
- **No changes needed** - Already loads models generically from saved_models/

## Step-by-Step Workflow

### Step 1: Clean Old Artifacts (Optional)
```bash
cd "C:\Users\Manus\OneDrive\Desktop\L-thirupathi\network-threat-detection\network-threat\backend"
python ml_model/cleanup_cicids2017.py
```
This removes:
- All .pkl files from `ml_model/saved_models/`
- All report files from `ml_model/reports/`

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```
(xgboost is already in requirements.txt)

### Step 3: Train Models
```bash
python ml_model/train_ciciot2023_models.py
```

**For faster training (subsample SVM/KNN)**:
```bash
python ml_model/train_ciciot2023_models.py --fast
```

### Step 4: Start API Server
```bash
python api/app.py
```

The server will:
- Automatically load the new CICIoT2023-trained models
- Use the new scaler, label encoder, and feature columns
- Serve the new reports through the research API

### Step 5: View Results
- **API Results**: `http://localhost:5000/api/research/model-comparison`
- **Results Page**: Navigate to `/results` in the frontend
- **Exports**: Download CSV/PNG files via `/api/research/export/...`

## Training Details

### Preprocessing
1. **Load**: Read all CSV files from train/, test/, validation/ folders
2. **Clean**: 
   - Strip column names
   - Auto-detect label column
   - Drop identifier columns (Flow ID, Source IP, etc.)
   - Replace Inf with NaN, fill NaN with median
   - Drop rows with remaining NaN
3. **Deduplicate**: Drop BENIGN duplicates, keep all attack rows
4. **Encode**: Use LabelEncoder to convert class names → integers
5. **Split**: Use pre-split train/val/test folders (no random split)
6. **Clip**: Apply 1st/99th percentile clipping (fit on train only)
7. **Scale**: StandardScaler (fit on train only)

### Model Hyperparameters
All models use balanced class weights or sample weights to handle imbalanced data.

| Model | Key Parameters |
|-------|-----------------|
| RF | n_estimators=200, max_depth=20, min_samples_leaf=5 |
| DT | max_depth=15, min_samples_leaf=5 |
| LR | C=0.5, max_iter=1000 |
| SVM | kernel='rbf', C=1.0, CalibratedClassifierCV |
| KNN | n_neighbors=7, weights='distance' |
| XGB | n_estimators=150, max_depth=6, learning_rate=0.1 |
| NB | GaussianNB (no special params) |

### Fast Mode (`--fast` flag)
If specified, SVM and KNN are stratified-subsampled:
- SVM: 15,000 rows
- KNN: 20,000 rows
- XGBoost: 25,000 rows

This keeps attack class distributions intact while reducing training time.

## Report Files

### model_comparison_ciciot2023.csv
Columns:
- model_name: Model name
- accuracy: Overall accuracy
- balanced_accuracy: Accuracy balanced across classes
- precision, recall, f1_score: Weighted metrics
- macro_precision, macro_recall, macro_f1: Per-class fairness metrics
- attack_detection_rate: Recall on non-BENIGN classes (primary metric)
- train_time_s: Training time in seconds
- pred_time_s: Prediction time in seconds

### per_class_metrics_ciciot2023.csv
Per-class metrics for each model:
- model: Model name
- class: Attack class name
- precision, recall, f1: Class-specific metrics

### latency_report_ciciot2023.csv
Training and prediction latency:
- model: Model name
- train_time_s: Training time
- pred_time_ms: Prediction time on full test set

### classification_report_ciciot2023.txt
Detailed sklearn classification report (primary model = Random Forest)

### confusion_matrix_ciciot2023.png
Confusion matrix heatmap (primary model = Random Forest)

## API Endpoints (Updated)

All endpoints now support both CICIDS2017 and CICIoT2023 automatically:

- `GET /api/research/model-comparison` - Returns best model and all metrics
- `GET /api/research/per-class-metrics` - Per-class precision/recall/f1
- `GET /api/research/latency-report` - Training and prediction times
- `GET /api/research/summary` - Summary text report
- `GET /api/research/confusion-matrix/random_forest` - Confusion matrix image
- `GET /api/research/export/model-comparison-csv` - Download CSV
- `GET /api/research/export/per-class-csv` - Download per-class metrics
- `GET /api/research/export/summary-txt` - Download summary

## Frontend Integration

### Results Page (`/results`)
The `/results` page automatically:
1. **Detects dataset** by reading which files exist
2. **Displays new metrics** from CICIoT2023 reports
3. **Shows correct metadata** (number of features, classes, split mode)
4. **Provides exports** of reports

No code changes needed in the frontend - it reads the API responses dynamically.

## Troubleshooting

### "No CSV files found in dataset_dir"
- Verify the dataset path: `C:\Users\Manus\OneDrive\Desktop\L-thirupathi\dataset\archive (3)\CICIOT23`
- Check that train/, validation/, test/ folders exist
- Verify CSV files are in those folders (not in subfolders)

### "Cannot find label column"
- Check CSV column names
- The script searches for: "label", "Label", "Attack", "class", "Category" (case-insensitive)
- If your column has a different name, update `LABEL_CANDIDATES` in `preprocess_ciciot2023.py`

### Models not loading in API
- Ensure `python ml_model/train_ciciot2023_models.py` completed successfully
- Check that `saved_models/*.pkl` files exist
- Verify the API server restarted after training

### Research page shows old CICIDS2017 reports
- Delete old report files: `python ml_model/cleanup_cicids2017.py`
- Retrain models: `python ml_model/train_ciciot2023_models.py`
- Restart the API server

## Environment Variables

Optional: Set custom dataset path via environment variable:
```bash
set CICIOT_DATASET_DIR=C:\path\to\CICIOT23
python ml_model/train_ciciot2023_models.py
```

## Performance Expectations

Expected macro-F1 scores (typical ranges):
- **Random Forest**: 85-95%
- **XGBoost**: 82-92%
- **Decision Tree**: 78-88%
- **KNN**: 75-85%
- **Logistic Regression**: 65-78%
- **SVM**: 60-75%
- **Naive Bayes**: 50-70%

Actual scores depend on the IoT attack classes in CICIoT2023 and their imbalance ratio.

## Files Modified/Created

### Created
- `ml_model/preprocess_ciciot2023.py` - Dataset loader
- `ml_model/train_ciciot2023_models.py` - Training script
- `ml_model/cleanup_cicids2017.py` - Cleanup script
- `CICIOT2023_MIGRATION.md` - This file

### Modified
- `api/research_api.py` - Made dataset-agnostic

### Unchanged
- `predict.py` - Loads models generically
- `app.py` - No changes needed
- `evaluate_models.py` - Used by training script
- All frontend code

## Next Steps

1. Run cleanup script (optional): `python ml_model/cleanup_cicids2017.py`
2. Install dependencies: `pip install -r requirements.txt`
3. Train models: `python ml_model/train_ciciot2023_models.py` (or with `--fast`)
4. Start API: `python api/app.py`
5. View results at `/results` page in frontend

The rest is automatic - the API and frontend will detect and display the new CICIoT2023 results.
