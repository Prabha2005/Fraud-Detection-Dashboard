# retrain.py

import pandas as pd
import joblib
import os
from xgboost import XGBClassifier
from database import get_db
from preprocess import preprocess


FEATURE_ORDER = [
    "transaction_amount",
    "device_change",
    "merchant_risk",
    "geo_velocity",
    "hour_of_day",
    "txn_count_24h",
    "amount_zscore",
    "amount_vs_max",
    "amount_sum_24h",
]


def retrain_model():
    """
    Retrain model using transaction history from database
    """

    conn = get_db()

    # ----------------------------
    # Load data from DB
    # ----------------------------
    df = pd.read_sql_query("SELECT * FROM transactions", conn)

    if df.empty:
        return {"status": "No data available for retraining"}

    # ----------------------------
    # Basic feature mapping
    # ----------------------------
    df["transaction_amount"] = df["amount"]
    df["geo_velocity"] = 50
    df["hour_of_day"] = 12

    # Add velocity placeholders (can be improved later)
    for col in ["txn_count_24h", "amount_zscore", "amount_vs_max", "amount_sum_24h"]:
        if col not in df.columns:
            df[col] = 0.0

    # ----------------------------
    # Check label exists
    # ----------------------------
    if "fraud_label" not in df.columns:
        return {"status": "No fraud labels found in DB"}

    X = preprocess(df)
    X = X[FEATURE_ORDER]
    y = df["fraud_label"]

    # ----------------------------
    # Train new model
    # ----------------------------
    model = XGBClassifier(
        n_estimators=150,
        max_depth=5,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        eval_metric="logloss",
        random_state=42,
    )

    model.fit(X, y)

    # ----------------------------
    # Save model
    # ----------------------------
    os.makedirs("model", exist_ok=True)
    joblib.dump(model, "model/xgboost_model.pkl")

    return {"status": "Model retrained successfully"}