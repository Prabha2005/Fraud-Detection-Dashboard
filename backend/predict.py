import time
from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from preprocess import FEATURE_ORDER, preprocess


# ----------------------------
# Model Paths
# ----------------------------
BACKEND_DIR = Path(__file__).resolve().parent
MODEL_DIR = BACKEND_DIR / "model"

MODEL_PATH = MODEL_DIR / "xgboost_model.pkl"
THRESHOLD_PATH = MODEL_DIR / "fraud_threshold.pkl"


# ----------------------------
# Load Model and Threshold
# ----------------------------
@lru_cache()
def load_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Model file was not found: {MODEL_PATH}"
        )

    return joblib.load(MODEL_PATH)


@lru_cache()
def load_threshold() -> float:
    if not THRESHOLD_PATH.exists():
        raise FileNotFoundError(
            f"Threshold file was not found: {THRESHOLD_PATH}"
        )

    threshold = float(joblib.load(THRESHOLD_PATH))

    if not 0 <= threshold <= 1:
        raise ValueError(
            f"Invalid fraud threshold: {threshold}"
        )

    return threshold


# ----------------------------
# Risk Level Mapping
# ----------------------------
def risk_label(probability: float) -> str:
    if probability >= 0.8:
        return "High Risk"

    if probability >= 0.4:
        return "Medium Risk"

    return "Low Risk"


# ----------------------------
# Feature-based Explanation
# ----------------------------
def get_top_features(model, transaction_features):
    importances = model.feature_importances_
    values = transaction_features.iloc[0].to_numpy(
        dtype=float
    )

    impacts = np.abs(importances * values)
    sorted_indices = np.argsort(impacts)[::-1]

    return [
        f"{transaction_features.columns[index]} contributed"
        for index in sorted_indices[:2]
    ]


# ----------------------------
# Fraud Prediction
# ----------------------------
def predict_fraud(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        raise ValueError("Input DataFrame is empty.")

    model = load_model()
    threshold = load_threshold()

    X = preprocess(df)
    X = X[FEATURE_ORDER]

    if X.shape[1] != model.n_features_in_:
        raise ValueError(
            "Feature count does not match the trained model. "
            f"Expected {model.n_features_in_}, received {X.shape[1]}."
        )

    start_time = time.perf_counter()

    fraud_probabilities = model.predict_proba(X)[:, 1]
    fraud_predictions = (
        fraud_probabilities >= threshold
    ).astype(int)

    latency_ms = (
        time.perf_counter() - start_time
    ) * 1000

    result_df = df.copy()
    result_df["fraud_probability"] = fraud_probabilities
    result_df["fraud_prediction"] = fraud_predictions
    result_df["risk_level"] = result_df[
        "fraud_probability"
    ].apply(risk_label)
    result_df["decision_threshold"] = threshold
    result_df["inference_latency_ms"] = round(
        latency_ms,
        2,
    )

    reasons = []

    for index in range(len(X)):
        if fraud_predictions[index] == 1:
            transaction_reasons = get_top_features(
                model,
                X.iloc[[index]],
            )
        else:
            transaction_reasons = []

        reasons.append(transaction_reasons)

    result_df["reasons"] = reasons

    return result_df