backend/
├── requirements.txt
├── ml_model/
│ ├── **init**.py
│ ├── preprocess.py ← loads all 8 CSVs, cleans, splits, scales
│ ├── train_models.py ← trains 7 models, saves .pkl files
│ ├── evaluate_models.py ← metrics, CSV report, confusion matrix PNG
│ ├── predict.py ← predict_threat() reusable function
│ ├── saved_models/ ← .pkl files written here after training
│ └── reports/ ← model_comparison.csv, classification_report.txt, confusion_matrix.png
└── api/
├── **init**.py
├── app.py ← Flask API (5 endpoints)
├── threat_detector.py ← combines predict + trust + decision
├── trust_manager.py ← α/β/γ weighted trust score, stateful history
└── decision_engine.py ← Allow/Restrict/Alert/Quarantine/Block rules

---

To start

# Terminal 1 — backend (from project root)

cd backend
pip install -r requirements.txt
python api/app.py

# Terminal 2 — frontend

npm run dev

Then: open http://localhost:3000/dashboard → select interface → click START CAPTURE → watch live packets flow through the ML pipeline into every panel.

Commands to run

cd backend
pip install -r requirements.txt

# Full training (all rows, all models) — takes 20-60 min on CICIDS2017

python ml_model/train_models.py

# Fast mode (80k rows, SVM/KNN subsampled to 10k) — takes ~5 min

python ml_model/train_models.py --fast

# Custom row limit

python ml_model/train_models.py --sample 100000

# Start API after training

python api/app.py

---

API endpoints

┌────────┬───────────────────────┬───────────────────────────────────────────────────────┐
│ Method │ Route │ Description │
├────────┼───────────────────────┼───────────────────────────────────────────────────────┤
│ GET │ / │ Backend status │
├────────┼───────────────────────┼───────────────────────────────────────────────────────┤
│ GET │ /health │ Lists loaded models │
├────────┼───────────────────────┼───────────────────────────────────────────────────────┤
│ POST │ /api/predict │ JSON flow features → prediction + trust + action │
├────────┼───────────────────────┼───────────────────────────────────────────────────────┤
│ GET │ /api/model-comparison │ Returns model_comparison.csv as JSON │
├────────┼───────────────────────┼───────────────────────────────────────────────────────┤
│ GET │ /api/dashboard-stats │ Live stats (or mock fallback before first prediction) │
└────────┴───────────────────────┴───────────────────────────────────────────────────────┘

Example prediction request:
POST /api/predict
{
"features": { "Flow Duration": 100000, "Total Fwd Packets": 5 },
"model": "random_forest",
"entity_id": "192.168.1.10"
}

---

Key design decisions

- FAST_MODE (--fast): SVM and KNN subsample to 10,000 rows; full dataset trains in ~5 mins instead of hours
- Trust formula: 0.3×UserTrust + 0.3×DeviceTrust + 0.4×BehaviorTrust — behavior is derived from rolling event history per entity
- Block threshold: 3 consecutive Critical events from the same entity triggers a Block
- Mock fallback: /api/dashboard-stats returns realistic CICIDS2017-scale numbers before any live predictions are made, so the frontend stays functional
  immediately
