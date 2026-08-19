import pandas as pd


# ----------------------------
# Feature Definitions
# ----------------------------
BASIC_FEATURES = [
    "transaction_amount",
    "device_change",
    "merchant_risk",
    "geo_velocity",
    "hour_of_day",
]

BEHAVIOURAL_FEATURES = [
    "txn_count_24h",
    "amount_zscore",
    "amount_vs_max",
    "amount_sum_24h",
]

FEATURE_ORDER = BASIC_FEATURES + BEHAVIOURAL_FEATURES


# ----------------------------
# Geo Velocity Cleaning
# ----------------------------
def calculate_geo_velocity(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["geo_velocity"] = df["geo_velocity"].abs()
    df["geo_velocity"] = df["geo_velocity"].clip(upper=500)
    return df


# ----------------------------
# Preprocessing Function
# ----------------------------
def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        raise ValueError("Input DataFrame is empty.")

    df = df.copy()

    # The five basic transaction features must be supplied.
    missing_features = [
        feature for feature in BASIC_FEATURES
        if feature not in df.columns
    ]

    if missing_features:
        raise ValueError(
            f"Missing required columns: {missing_features}"
        )

    # Behavioural features may be unavailable for CSV/PDF records.
    behavioural_defaults = {
        "txn_count_24h": 0,
        "amount_zscore": 0.0,
        "amount_vs_max": 1.0,
        "amount_sum_24h": 0.0,
    }

    for feature, default_value in behavioural_defaults.items():
        if feature not in df.columns:
            df[feature] = default_value

    # Convert all nine model features to numeric values.
    for feature in FEATURE_ORDER:
        df[feature] = pd.to_numeric(df[feature], errors="coerce")

    # Handle invalid or missing values.
    df[BASIC_FEATURES] = df[BASIC_FEATURES].fillna(0)

    for feature, default_value in behavioural_defaults.items():
        df[feature] = df[feature].fillna(default_value)

    # Apply domain-specific cleaning.
    df = calculate_geo_velocity(df)

    return df[FEATURE_ORDER]