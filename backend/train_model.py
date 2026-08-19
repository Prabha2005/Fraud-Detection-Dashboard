import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import shap
from xgboost import XGBClassifier
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split

from preprocess import FEATURE_ORDER, preprocess


# ----------------------------
# Project Paths
# ----------------------------
BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BACKEND_DIR.parent
DATA_PATH = PROJECT_DIR / "sample_data" / "upi_fraud_demo.csv"
MODEL_DIR = BACKEND_DIR / "model"

MODEL_PATH = MODEL_DIR / "xgboost_model.pkl"
THRESHOLD_PATH = MODEL_DIR / "fraud_threshold.pkl"
SHAP_PATH = MODEL_DIR / "shap_explainer.pkl"
METRICS_PATH = MODEL_DIR / "evaluation_metrics.json"
STATS_PATH = MODEL_DIR / "training_stats.json"

MODEL_DIR.mkdir(parents=True, exist_ok=True)


# ----------------------------
# Load Dataset
# ----------------------------
df = pd.read_csv(DATA_PATH)

if "fraud_label" not in df.columns:
    raise ValueError("Missing required column: fraud_label")

X = preprocess(df)
y = pd.to_numeric(df["fraud_label"], errors="raise").astype(int)

if not set(y.unique()).issubset({0, 1}):
    raise ValueError("fraud_label must contain only 0 and 1.")


# ----------------------------
# Class Imbalance Handling
# ----------------------------
fraud_count = int((y == 1).sum())
legit_count = int((y == 0).sum())

if fraud_count == 0 or legit_count == 0:
    raise ValueError(
        "Dataset must contain both fraud and legitimate records."
    )

print("\nComplete dataset distribution:")
print(f"Legitimate transactions: {legit_count}")
print(f"Fraud transactions: {fraud_count}")


# ----------------------------
# Train, Validation and Test Split
# 60% train, 20% validation, 20% test
# ----------------------------
X_train, X_remaining, y_train, y_remaining = train_test_split(
    X,
    y,
    test_size=0.40,
    stratify=y,
    random_state=42,
)

X_validation, X_test, y_validation, y_test = train_test_split(
    X_remaining,
    y_remaining,
    test_size=0.50,
    stratify=y_remaining,
    random_state=42,
)

train_fraud_count = int((y_train == 1).sum())
train_legit_count = int((y_train == 0).sum())

if train_fraud_count == 0:
    raise ValueError(
        "Training data does not contain fraudulent records."
    )

scale_weight = train_legit_count / train_fraud_count

print("\nTraining-set class distribution:")
print(f"Legitimate transactions: {train_legit_count}")
print(f"Fraud transactions: {train_fraud_count}")
print(f"Scale weight: {scale_weight:.4f}")

print("\nDataset split:")
print(f"Training records: {len(X_train)}")
print(f"Validation records: {len(X_validation)}")
print(f"Testing records: {len(X_test)}")


# ----------------------------
# Train XGBoost Model
# ----------------------------
model = XGBClassifier(
    n_estimators=150,
    max_depth=5,
    learning_rate=0.1,
    subsample=0.8,
    colsample_bytree=0.8,
    eval_metric="logloss",
    random_state=42,
    scale_pos_weight=scale_weight,
)

model.fit(X_train, y_train)


# ----------------------------
# Threshold Selection
# Use validation data only
# ----------------------------
validation_probabilities = model.predict_proba(X_validation)[:, 1]

precisions, recalls, thresholds = precision_recall_curve(
    y_validation,
    validation_probabilities,
)

if len(thresholds) == 0:
    best_threshold = 0.5
else:
    threshold_f1_scores = (
        2 * precisions[:-1] * recalls[:-1]
        / (precisions[:-1] + recalls[:-1] + 1e-8)
    )

    best_index = int(np.argmax(threshold_f1_scores))
    best_threshold = float(thresholds[best_index])

joblib.dump(best_threshold, THRESHOLD_PATH)

print(f"\nSelected fraud threshold: {best_threshold:.4f}")


# ----------------------------
# Evaluate on Unseen Test Data
# ----------------------------
test_probabilities = model.predict_proba(X_test)[:, 1]
test_predictions = (
    test_probabilities >= best_threshold
).astype(int)

metrics = {
    "dataset_records": int(len(df)),
    "training_records": int(len(X_train)),
    "validation_records": int(len(X_validation)),
    "testing_records": int(len(X_test)),
    "legitimate_records": legit_count,
    "fraud_records": fraud_count,
    "scale_pos_weight": float(scale_weight),
    "selected_threshold": float(best_threshold),
    "accuracy": float(
        accuracy_score(y_test, test_predictions)
    ),
    "precision": float(
        precision_score(
            y_test,
            test_predictions,
            zero_division=0,
        )
    ),
    "recall": float(
        recall_score(
            y_test,
            test_predictions,
            zero_division=0,
        )
    ),
    "f1_score": float(
        f1_score(
            y_test,
            test_predictions,
            zero_division=0,
        )
    ),
    "roc_auc": float(
        roc_auc_score(y_test, test_probabilities)
    ),
    "pr_auc": float(
        average_precision_score(
            y_test,
            test_probabilities,
        )
    ),
    "confusion_matrix": confusion_matrix(
        y_test,
        test_predictions,
    ).tolist(),
    "classification_report": classification_report(
        y_test,
        test_predictions,
        target_names=["Legitimate", "Fraud"],
        output_dict=True,
        zero_division=0,
    ),
    "training_legitimate_records": train_legit_count,
    "training_fraud_records": train_fraud_count,
}

with open(METRICS_PATH, "w", encoding="utf-8") as file:
    json.dump(metrics, file, indent=4)

print("\nTest-set model performance:")
print(f"Accuracy:  {metrics['accuracy']:.4f}")
print(f"Precision: {metrics['precision']:.4f}")
print(f"Recall:    {metrics['recall']:.4f}")
print(f"F1 Score:  {metrics['f1_score']:.4f}")
print(f"ROC-AUC:   {metrics['roc_auc']:.4f}")
print(f"PR-AUC:    {metrics['pr_auc']:.4f}")

print("\nConfusion matrix:")
print(np.array(metrics["confusion_matrix"]))

print("\nClassification report:")
print(
    classification_report(
        y_test,
        test_predictions,
        target_names=["Legitimate", "Fraud"],
        zero_division=0,
    )
)


# ----------------------------
# Feature Importance
# ----------------------------
print("\nFeature importances:")

for feature, importance in zip(
    FEATURE_ORDER,
    model.feature_importances_,
):
    print(f"{feature:<25} {importance:.6f}")


# ----------------------------
# Generate SHAP Explainer
# ----------------------------
print("\nGenerating SHAP explainer...")

explainer = shap.TreeExplainer(model)
joblib.dump(explainer, SHAP_PATH)

shap_values = explainer(X_train)
mean_shap_values = np.abs(
    shap_values.values
).mean(axis=0)

print("\nMean absolute SHAP values:")

for feature, value in sorted(
    zip(FEATURE_ORDER, mean_shap_values),
    key=lambda item: item[1],
    reverse=True,
):
    print(f"{feature:<25} {value:.6f}")


# ----------------------------
# Save Model
# ----------------------------
joblib.dump(model, MODEL_PATH)


# ----------------------------
# Save Training Statistics
# ----------------------------
training_stats = {
    feature: {
        "mean": float(X_train[feature].mean()),
        "std": float(X_train[feature].std()),
    }
    for feature in FEATURE_ORDER
}

with open(STATS_PATH, "w", encoding="utf-8") as file:
    json.dump(training_stats, file, indent=4)


print("\nTraining completed.")
print(f"Model: {MODEL_PATH}")
print(f"Threshold: {THRESHOLD_PATH}")
print(f"SHAP explainer: {SHAP_PATH}")
print(f"Evaluation report: {METRICS_PATH}")
print(f"Training statistics: {STATS_PATH}")