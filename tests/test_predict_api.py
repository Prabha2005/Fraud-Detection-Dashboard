import sys
from pathlib import Path

from fastapi.testclient import TestClient


PROJECT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_DIR / "backend"

sys.path.insert(0, str(BACKEND_DIR))

from app import app
from auth import create_token


client = TestClient(app)


def test_predict_rejects_unauthenticated_request():
    csv_content = (
        "transaction_amount,device_change,"
        "merchant_risk,geo_velocity,hour_of_day\n"
        "500,0,0.2,50,12\n"
    )

    response = client.post(
        "/predict",
        files={
            "file": (
                "transactions.csv",
                csv_content,
                "text/csv",
            )
        },
    )

    assert response.status_code in {401, 403}


def test_authenticated_csv_prediction():
    token = create_token("pytest_user")

    csv_content = (
        "transaction_amount,device_change,"
        "merchant_risk,geo_velocity,hour_of_day\n"
        "500,0,0.2,50,12\n"
        "5000,1,0.95,250,2\n"
    )

    response = client.post(
        "/predict",
        headers={
            "Authorization": f"Bearer {token}"
        },
        files={
            "file": (
                "transactions.csv",
                csv_content,
                "text/csv",
            )
        },
    )

    assert response.status_code == 200

    results = response.json()

    assert isinstance(results, list)
    assert len(results) == 2

    required_fields = {
        "prediction",
        "probability",
        "risk_level",
        "decision_threshold",
        "reasons",
        "latency_ms",
    }

    for result in results:
        assert required_fields.issubset(result)
        assert result["prediction"] in {
            "Fraud",
            "Legit",
        }
        assert 0 <= result["probability"] <= 1
        assert 0 <= result["decision_threshold"] <= 1
        assert result["risk_level"] in {
            "Low Risk",
            "Medium Risk",
            "High Risk",
        }
        assert isinstance(result["reasons"], list)
        assert result["latency_ms"] >= 0