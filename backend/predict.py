import pandas as pd
import joblib
from functools import lru_cache
from preprocess import preprocess
import time
import numpy as np


# ----------------------------
# Load Model (Cached)
# ----------------------------
@lru_cache()
def load_model():
    return joblib.load("model/xgboost_model.pkl")


# ----------------------------
# Risk Level Mapping
# ----------------------------
def risk_label(prob: float) -> str:
    if prob >= 0.8:
        return "High Risk"
    elif prob >= 0.4:
        return "Medium Risk"
    else:
        return "Low Risk"


# ----------------------------
# ML-based Top Feature Explanation
# ----------------------------
def get_top_features(model, X_row):
    contributions = model.feature_importances_
    feature_names = X_row.columns

    impact = contributions * X_row.values[0]

    sorted_idx = np.argsort(impact)[::-1]

    top_features = []
    for i in sorted_idx[:2]:
        top_features.append(f"{feature_names[i]} contributed")

    return top_features


# ----------------------------
# Fraud Prediction Function
# ----------------------------
def predict_fraud(df: pd.DataFrame) -> pd.DataFrame:

    if df.empty:
        raise ValueError("Input DataFrame is empty.")

    model = load_model()
    X = preprocess(df)

    start = time.time()
    fraud_prob = model.predict_proba(X)[:, 1]
    fraud_pred = (fraud_prob >= 0.5).astype(int)
    latency = (time.time() - start) * 1000

    result_df = df.copy()
    result_df["fraud_probability"] = fraud_prob
    result_df["fraud_prediction"] = fraud_pred
    result_df["risk_level"] = result_df["fraud_probability"].apply(risk_label)
    result_df["inference_latency_ms"] = round(latency, 2)

    # ----------------------------
    # Generate Reasons (ONLY for Fraud)
    # ----------------------------
    reasons_list = []

    for i in range(len(X)):
        if fraud_pred[i] == 1:
            reasons = get_top_features(model, X.iloc[[i]])
        else:
            reasons = []

        reasons_list.append(reasons)

    result_df["reasons"] = reasons_list

    return result_df
