# 🍷 WineIQ — ML-Powered Wine Quality Predictor

A full-stack web app that predicts wine quality scores using a Random Forest ML model trained on 1,143 real wine samples.

---

## Tech Stack
- **ML**: Scikit-learn (Random Forest + StandardScaler Pipeline)
- **Backend**: Flask + session-based auth
- **Database**: MySQL
- **Frontend**: Jinja2 + Bootstrap 5

---

## Setup Instructions

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Set up the database
```bash
mysql -u root -p < schema.sql
```

### 3. Configure DB credentials
Open `app.py` and update the `DB` dict:
```python
DB = dict(host="localhost", user="root", password="YOUR_PASSWORD", db="wine_db")
```

### 4. Train the model
```bash
python train_model.py
```
This generates `rf_wine_model.pkl`.

### 5. Run the app
```bash
python app.py
```
Visit: http://localhost:5000

---

## Model Details

| Property       | Value                          |
|----------------|-------------------------------|
| Algorithm      | Random Forest Regressor        |
| Trees          | 200 (max_depth=10)             |
| Preprocessing  | StandardScaler                 |
| Dataset        | WineQT.csv (1,143 samples)     |
| MAE            | ~0.42 quality points           |
| Quality Scale  | 3 (Poor) → 8 (Excellent)       |

**Top features by importance:**
1. Alcohol (30%)
2. Volatile Acidity (16%)
3. Sulphates (15%)

---

## Quality Labels
| Score | Label     |
|-------|-----------|
| < 5   | Poor      |
| 5–5.9 | Average   |
| 6–6.9 | Good      |
| ≥ 7   | Excellent |

---

## Project Structure
```
wine_app/
├── app.py              # Flask routes & ML inference
├── train_model.py      # Model training script
├── schema.sql          # MySQL schema
├── requirements.txt    # Python dependencies
├── rf_wine_model.pkl   # Trained model (generated)
├── WineQT.csv          # Dataset
└── templates/
    ├── base.html       # Master layout
    ├── home.html
    ├── register.html
    ├── login.html
    ├── dashboard.html
    ├── predict.html
    ├── history.html
    ├── about.html
    └── contact.html
```
