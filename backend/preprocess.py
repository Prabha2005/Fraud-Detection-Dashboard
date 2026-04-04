import pandas as pd
import numpy as np


# ----------------------------
# Geo Velocity Cleaning
# ----------------------------
def calculate_geo_velocity(df: pd.DataFrame) -> pd.DataFrame:
    df["geo_velocity"] = df["geo_velocity"].abs()
    df["geo_velocity"] = df["geo_velocity"].clip(upper=500)
    return df


# ----------------------------
# Preprocessing Function
# ----------------------------
def preprocess(df: pd.DataFrame) -> pd.DataFrame:

    df = df.copy()

    required_features = [
        "transaction_amount",
        "device_change",
        "merchant_risk",
        "geo_velocity",
        "hour_of_day"
    ]

    # ----------------------------
    # Check missing columns
    # ----------------------------
    for col in required_features:
        if col not in df.columns:
            raise ValueError(f"Missing column: {col}")

    # ----------------------------
    # Convert types safely
    # ----------------------------
    df["transaction_amount"] = pd.to_numeric(df["transaction_amount"], errors="coerce")
    df["device_change"] = pd.to_numeric(df["device_change"], errors="coerce")
    df["merchant_risk"] = pd.to_numeric(df["merchant_risk"], errors="coerce")
    df["geo_velocity"] = pd.to_numeric(df["geo_velocity"], errors="coerce")
    df["hour_of_day"] = pd.to_numeric(df["hour_of_day"], errors="coerce")

    # ----------------------------
    # Handle missing values
    # ----------------------------
    df[required_features] = df[required_features].fillna(0)

    # ----------------------------
    # Clean geo_velocity
    # ----------------------------
    df = calculate_geo_velocity(df)

    return df[required_features]