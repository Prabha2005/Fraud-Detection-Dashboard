import os
import pandas as pd
import joblib
import shap
import numpy as np
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score, classification_report
)

from preprocess import preprocess


# ----------------------------
# Feature Order (updated with velocity features)
# ----------------------------
FEATURE_ORDER = [
    "transaction_amount",
    "device_change",
    "merchant_risk",
    "geo_velocity",
    "hour_of_day",
    # NEW velocity features
    "txn_count_24h",
    "amount_zscore",
    "amount_vs_max",
    "amount_sum_24h",
]


# ----------------------------
# Load Dataset
# ----------------------------
df = pd.read_csv("sample_data/upi_fraud_demo.csv")

missing_cols = [col for col in ["fraud_label"] if col not in df.columns]
if missing_cols:
    raise ValueError(f"Missing required columns: {missing_cols}")

# Fill velocity features with 0 if not in CSV yet
# (they'll be computed live in production from DB history)
for col in ["txn_count_24h", "amount_zscore", "amount_vs_max", "amount_sum_24h"]:
    if col not in df.columns:
        df[col] = 0.0


# ----------------------------
# Apply preprocessing
# ----------------------------
X = preprocess(df)
X = X[FEATURE_ORDER]
y = df["fraud_label"]


# ----------------------------
# Class Imbalance — compute scale weight
# ----------------------------
fraud_count = (y == 1).sum()
legit_count = (y == 0).sum()
scale_weight = legit_count / max(fraud_count, 1)

print(f"\n📊 Class distribution:")
print(f"   Legit transactions : {legit_count}")
print(f"   Fraud transactions : {fraud_count}")
print(f"   Scale weight       : {scale_weight:.2f}x")


# ----------------------------
# Train-Test Split
# ----------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.2,
    stratify=y,
    random_state=42
)


# ----------------------------
# Train Model (with class weight)
# ----------------------------
model = XGBClassifier(
    n_estimators=150,
    max_depth=5,
    learning_rate=0.1,
    subsample=0.8,
    colsample_bytree=0.8,
    eval_metric="logloss",
    random_state=42,
    scale_pos_weight=scale_weight,   # NEW — penalises missing fraud more
)

model.fit(X_train, y_train)


# ----------------------------
# Threshold Tuning (NEW)
# ----------------------------
from sklearn.metrics import precision_recall_curve

y_prob_train = model.predict_proba(X_train)[:, 1]
y_prob_test  = model.predict_proba(X_test)[:, 1]

precisions, recalls, thresholds = precision_recall_curve(y_train, y_prob_train)
f1_scores = 2 * (precisions * recalls) / (precisions + recalls + 1e-8)
best_idx       = np.argmax(f1_scores)
#best_threshold = float(thresholds[best_idx])
best_threshold = float(thresholds[best_idx]) if len(thresholds) > 0 else 0.5

print(f"\n🎯 Best threshold found: {best_threshold:.3f}")

# ✅ ADD THIS LINE HERE 👇
os.makedirs("model", exist_ok=True)


# Save threshold alongside model so app.py can use it
joblib.dump(best_threshold, "model/fraud_threshold.pkl")


# ----------------------------
# Evaluation (using tuned threshold)
# ----------------------------
y_pred = (y_prob_test >= best_threshold).astype(int)

print("\n📊 Model Performance (with tuned threshold):")
print(f"Accuracy  : {accuracy_score(y_test, y_pred):.4f}")
print(f"Precision : {precision_score(y_test, y_pred):.4f}")
print(f"Recall    : {recall_score(y_test, y_pred):.4f}   ← most important for fraud")
print(f"F1 Score  : {f1_score(y_test, y_pred):.4f}")
print(f"ROC-AUC   : {roc_auc_score(y_test, y_prob_test):.4f}")

print("\n📋 Full classification report:")
print(classification_report(y_test, y_pred, target_names=["Legit", "Fraud"]))


# ----------------------------
# Feature Importance
# ----------------------------
print("\n🔍 Feature importances:")
importance = model.feature_importances_
for col, imp in zip(FEATURE_ORDER, importance):
    bar = "█" * int(imp * 50)
    print(f"  {col:<25} {imp:.4f}  {bar}")


# ----------------------------
# SHAP Explainer (NEW)
# ----------------------------
print("\n⚙️  Building SHAP explainer (this takes ~10 seconds)...")

explainer   = shap.TreeExplainer(model)
X_train = X_train[FEATURE_ORDER].copy()
shap_values = explainer(X_train)

print("\n🔍 Mean absolute SHAP values (true feature impact):")
mean_shap = shap_values.abs.mean(0).values
for col, val in sorted(zip(FEATURE_ORDER, mean_shap), key=lambda x: -x[1]):
    bar = "█" * int(val * 100)
    print(f"  {col:<25} {val:.4f}  {bar}")

# Save explainer
joblib.dump(explainer, "model/shap_explainer.pkl")
print("\n✅ SHAP explainer saved → model/shap_explainer.pkl")


# ----------------------------
# Save Model
# ----------------------------
os.makedirs("model", exist_ok=True)
joblib.dump(model, "model/xgboost_model.pkl")

print("✅ Model saved          → model/xgboost_model.pkl")
print("✅ Threshold saved      → model/fraud_threshold.pkl")
print("\n🎉 Training complete!")

import json

stats = {
    col: {
        "mean": float(X_train[col].mean()),
        "std": float(X_train[col].std())
    }
    for col in FEATURE_ORDER
}

with open("model/training_stats.json", "w") as f:
    json.dump(stats, f)