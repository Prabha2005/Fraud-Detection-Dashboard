# shap_utils.py

FEATURE_LABELS = {
    "transaction_amount": "transaction amount",
    "device_change": "device change",
    "merchant_risk": "merchant risk score",
    "geo_velocity": "geographic velocity",
    "hour_of_day": "transaction hour",

    # New velocity features
    "txn_count_24h": "transactions in last 24h",
    "amount_zscore": "amount anomaly score",
    "amount_vs_max": "amount vs user's max",
    "amount_sum_24h": "total spent in last 24h"
}


def explain_prediction(explainer, input_df):
    """
    Convert SHAP values into human-readable explanation
    """

    shap_vals = explainer(input_df)

    # First row only (single prediction)
    values = shap_vals[0].values
    base = float(shap_vals[0].base_values)

    contributions = []

    for col, v in zip(input_df.columns, values):
        contributions.append({
            "feature": col,
            "label": FEATURE_LABELS.get(col, col),
            "value": float(input_df[col].iloc[0]),
            "shap": round(float(v), 4),
            "direction": "increases fraud risk" if v > 0 else "decreases fraud risk"
        })

    # Sort by impact
    contributions.sort(key=lambda x: abs(x["shap"]), reverse=True)

    # Top reasons (human readable)
    top_reasons = []
    for c in contributions[:3]:
        if abs(c["shap"]) < 0.01:
            continue

        direction = "↑ raises" if c["shap"] > 0 else "↓ lowers"

        top_reasons.append(
            f"{direction} risk: {c['label']} = {c['value']} (impact: {c['shap']:+.3f})"
        )

    return {
        "base_score": round(base, 4),
        "contributions": contributions,
        "top_reasons": top_reasons
    }