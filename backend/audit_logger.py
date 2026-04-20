# audit_logger.py

import json
import os
from datetime import datetime

LOG_FILE = "logs/audit_log.jsonl"


def log_prediction(data: dict):
    """
    Logs prediction data to a JSONL file (one JSON per line)
    """

    os.makedirs("logs", exist_ok=True)

    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        **data
    }

    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(log_entry) + "\n")