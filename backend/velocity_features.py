# velocity_features.py

from datetime import datetime, timedelta
import numpy as np


def get_velocity_features(user_id, amount, conn):
    """
    Compute behavioral features from past transactions
    """

    # ----------------------------
    # Get last 24 hours data
    # ----------------------------
    cursor = conn.execute(
        """
        SELECT amount, timestamp 
        FROM transactions
        WHERE username = ?
        ORDER BY id DESC
        """,
        (user_id,)
    )

    rows = cursor.fetchall()

    now = datetime.now()
    last_24h = now - timedelta(hours=24)

    amounts_24h = []
    all_amounts = []

    for row in rows:
        txn_amount = row["amount"]
        txn_time_str = row["timestamp"] if "timestamp" in row.keys() else None

        all_amounts.append(txn_amount)

        # If timestamp exists → filter 24h
        if txn_time_str:
            try:
                txn_time = datetime.fromisoformat(txn_time_str)
                if txn_time >= last_24h:
                    amounts_24h.append(txn_amount)
            except:
                pass
        else:
            # fallback (if no timestamp stored yet)
            amounts_24h.append(txn_amount)

    # ----------------------------
    # Feature calculations
    # ----------------------------

    txn_count_24h = len(amounts_24h)
    amount_sum_24h = sum(amounts_24h)

    if all_amounts:
        mean_amt = np.mean(all_amounts)
        std_amt = np.std(all_amounts)

        amount_zscore = (amount - mean_amt) / std_amt if std_amt > 0 else 0

        max_amt = max(all_amounts)
        amount_vs_max = amount / max_amt if max_amt > 0 else 1

    else:
        amount_zscore = 0
        amount_vs_max = 1

    # ----------------------------
    # Return features
    # ----------------------------
    return {
        "txn_count_24h": txn_count_24h,
        "amount_zscore": float(amount_zscore),
        "amount_vs_max": float(amount_vs_max),
        "amount_sum_24h": float(amount_sum_24h)
    }