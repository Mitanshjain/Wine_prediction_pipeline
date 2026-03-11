import pandas as pd
import numpy as np
import pymysql
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score, mean_absolute_error
import joblib

# ── Load from MySQL (mirroring salary app pattern) ──────────────────────────
# Uncomment below and comment out the CSV block once data is loaded into MySQL

conn = pymysql.connect(host="localhost", user="root", password="root", db="wine_db")
df = pd.read_sql("SELECT * FROM wineqlt", conn)
conn.close()

# ── Load from CSV (for initial training) ─────────────────────────────────────
# df = pd.read_csv("WineQT.csv")
# df = df.drop(columns=["Id"])          # drop surrogate key — not a feature
# df = df.dropna()

FEATURES = [
    "fixed acidity", "volatile acidity", "citric acid",
    "residual sugar", "chlorides", "free sulfur dioxide",
    "total sulfur dioxide", "density", "pH", "sulphates", "alcohol"
]
TARGET = "quality"

X = df[FEATURES]
y = df[TARGET]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# ── Pipeline: StandardScaler → RandomForestRegressor ─────────────────────────
# Why RandomForest?
#   • Wine quality is determined by complex, non-linear interactions between
#     chemical properties — RF captures these far better than Linear Regression.
#   • Robust to outliers in chemical measurements.
#   • Gives feature importances for free (useful insight).
pipeline = Pipeline([
    ("scaler", StandardScaler()),
    ("model", RandomForestRegressor(
        n_estimators=200,
        max_depth=10,
        min_samples_split=5,
        random_state=42,
        n_jobs=-1
    ))
])

pipeline.fit(X_train, y_train)

# ── Evaluate ──────────────────────────────────────────────────────────────────
y_pred = pipeline.predict(X_test)
r2  = r2_score(y_test, y_pred)
mae = mean_absolute_error(y_test, y_pred)

print(f"R² Score : {r2:.4f}")
print(f"MAE      : {mae:.4f}  (quality is scored 3–8)")

# Feature importances
rf = pipeline.named_steps["model"]
importances = sorted(zip(FEATURES, rf.feature_importances_), key=lambda x: -x[1])
print("\nFeature Importances:")
for feat, imp in importances:
    print(f"  {feat:<30} {imp:.4f}")

# ── Save ──────────────────────────────────────────────────────────────────────
joblib.dump(pipeline, "rf_wine_model.pkl")
print("\nModel saved → rf_wine_model.pkl")
