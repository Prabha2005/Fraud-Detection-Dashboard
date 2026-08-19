import sys
from pathlib import Path

import pandas as pd
import pytest


BACKEND_DIR = (
    Path(__file__).resolve().parents[1] / "backend"
)

sys.path.insert(0, str(BACKEND_DIR))

from preprocess import FEATURE_ORDER, preprocess


def test_preprocess_returns_nine_features():
    input_df = pd.DataFrame([
        {
            "transaction_amount": 500,
            "device_change": 0,
            "merchant_risk": 0.2,
            "geo_velocity": 50,
            "hour_of_day": 12,
        }
    ])

    result = preprocess(input_df)

    assert result.columns.tolist() == FEATURE_ORDER
    assert result.shape == (1, 9)

    assert result.iloc[0]["txn_count_24h"] == 0
    assert result.iloc[0]["amount_zscore"] == 0.0
    assert result.iloc[0]["amount_vs_max"] == 1.0
    assert result.iloc[0]["amount_sum_24h"] == 0.0


def test_preprocess_preserves_behavioural_features():
    input_df = pd.DataFrame([
        {
            "transaction_amount": 500,
            "device_change": 1,
            "merchant_risk": 0.7,
            "geo_velocity": 80,
            "hour_of_day": 22,
            "txn_count_24h": 6,
            "amount_zscore": 2.4,
            "amount_vs_max": 1.5,
            "amount_sum_24h": 7000,
        }
    ])

    result = preprocess(input_df)

    assert result.iloc[0]["txn_count_24h"] == 6
    assert result.iloc[0]["amount_zscore"] == 2.4
    assert result.iloc[0]["amount_vs_max"] == 1.5
    assert result.iloc[0]["amount_sum_24h"] == 7000


def test_preprocess_rejects_invalid_amount():
    input_df = pd.DataFrame([
        {
            "transaction_amount": "abc",
            "device_change": 0,
            "merchant_risk": 0.2,
            "geo_velocity": 50,
            "hour_of_day": 12,
        }
    ])

    with pytest.raises(
        ValueError,
        match="transaction_amount",
    ):
        preprocess(input_df)