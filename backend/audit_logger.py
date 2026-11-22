import json
import os
from datetime import datetime
from pathlib import Path

LOG_FILE = os.getenv("AUDIT_LOG_PATH", "logs/audit_log.jsonl")


def log_prediction(data: dict):
    """
    Logs prediction data to a JSONL file (one JSON per line)
    """
    log_path = Path(LOG_FILE)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        **data
    }

    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry) + "\n")