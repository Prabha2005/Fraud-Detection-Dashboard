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
def calculate_geo_velocity(
    df: pd.DataFrame,
) -> pd.DataFrame:
    df = df.copy()
    df["geo_velocity"] = df["geo_velocity"].abs()
    df["geo_velocity"] = df["geo_velocity"].clip(
        upper=500
    )
    return df


# ----------------------------
# Preprocessing Function
# ----------------------------
def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        raise ValueError("Input DataFrame is empty.")

    df = df.copy()

    missing_features = [
        feature
        for feature in BASIC_FEATURES
        if feature not in df.columns
    ]

    if missing_features:
        raise ValueError(
            f"Missing required columns: {missing_features}"
        )

    behavioural_defaults = {
        "txn_count_24h": 0,
        "amount_zscore": 0.0,
        "amount_vs_max": 1.0,
        "amount_sum_24h": 0.0,
    }

    for feature, default_value in (
        behavioural_defaults.items()
    ):
        if feature not in df.columns:
            df[feature] = default_value

    # Convert all nine features and reject invalid values.
    for feature in FEATURE_ORDER:
        converted_values = pd.to_numeric(
            df[feature],
            errors="coerce",
        )

        invalid_rows = converted_values.isna()

        if invalid_rows.any():
            row_numbers = invalid_rows[
                invalid_rows
            ].index.tolist()

            raise ValueError(
                f"Invalid numeric value for {feature} "
                f"at rows: {row_numbers}"
            )

        df[feature] = converted_values

    # Validate feature ranges.
    if (df["transaction_amount"] <= 0).any():
        raise ValueError(
            "transaction_amount must be greater than zero."
        )

    if not df["device_change"].isin([0, 1]).all():
        raise ValueError(
            "device_change must be either 0 or 1."
        )

    if not df["merchant_risk"].between(0, 1).all():
        raise ValueError(
            "merchant_risk must be between 0 and 1."
        )

    if not df["hour_of_day"].between(0, 23).all():
        raise ValueError(
            "hour_of_day must be between 0 and 23."
        )

    if (df["txn_count_24h"] < 0).any():
        raise ValueError(
            "txn_count_24h cannot be negative."
        )

    if (df["amount_vs_max"] < 0).any():
        raise ValueError(
            "amount_vs_max cannot be negative."
        )

    if (df["amount_sum_24h"] < 0).any():
        raise ValueError(
            "amount_sum_24h cannot be negative."
        )

    df = calculate_geo_velocity(df)

    return df[FEATURE_ORDER]