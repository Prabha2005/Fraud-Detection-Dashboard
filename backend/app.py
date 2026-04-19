from ipaddress import ip_address
import sys
import os

from flask import request
from auth import create_token, verify_token
from models import Transaction
import json
from fastapi import Depends
from pydantic import BaseModel
from fastapi import Request
#ip_address = request.client.host
#user_agent = request.headers.get("user-agent")

#print("User IP:",  ip_address)
#print("Device Info:", user_agent)


sys.path.append(os.path.dirname(__file__))
print("FILES:", os.listdir())

from fastapi import FastAPI, UploadFile, File, HTTPException
import pandas as pd
import joblib
from functools import lru_cache
#from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="UPI Fraud Detection API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ----------------------------
# Model Loader (Cached)
# ----------------------------
@lru_cache()
def load_model():
    try:
        return joblib.load("model/xgboost_model.pkl")
    except Exception as e:
        raise RuntimeError(f"Error loading model: {str(e)}")


# ----------------------------
# Feature Order (IMPORTANT)
# ----------------------------
FEATURE_ORDER = [
    "transaction_amount",
    "device_change",
    "merchant_risk",
    "geo_velocity",
    "hour_of_day"
]


# ----------------------------
# Health Check Endpoint
# ----------------------------
@app.get("/")
def health_check():
    return {"status": "UPI Fraud Detection API is running"}


# ----------------------------
# Authentication Endpoint
# ----------------------------

from models import LoginRequest

@app.post("/login")
def login(data: LoginRequest):
    with open("users.json") as f:
        users = json.load(f)

    if data.username in users and users[data.username] == data.password:
        token = create_token(data.username)
        return {"token": token}
    
    raise HTTPException(status_code=401, detail="Invalid credentials")
# ----------------------------
# Prediction Endpoint
# ----------------------------
@app.post("/predict")
async def predict(file: UploadFile = File(...), user=Depends(verify_token)):
    # Validate file type
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed.")

    try:
        # Load model
        model = load_model()

        # Read CSV
        df = pd.read_csv(file.file)

        # Drop label column if present
        if "fraud_label" in df.columns:
            df = df.drop(columns=["fraud_label"])

        # Check required features
        missing_cols = [col for col in FEATURE_ORDER if col not in df.columns]
        if missing_cols:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns: {missing_cols}"
            )

        # Enforce feature order
        X = df[FEATURE_ORDER]

        from predict import predict_fraud

        # Inside predict endpoint:
        result_df = predict_fraud(df)

        response = []
        for _, row in result_df.iterrows():
            response.append({
        "prediction": "Fraud" if row["fraud_prediction"] == 1 else "Legit",
        "probability": round(row["fraud_probability"], 3),
        "risk_level": row["risk_level"],
        "reasons": row["reasons"],
        "latency_ms": row["inference_latency_ms"]
    })
        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
class Transaction(BaseModel):
    transaction_amount: float
    device_change: int
    merchant_risk: float
    geo_velocity: float
    hour_of_day: int

    #return {"message": "Prediction working securely"}



@app.post("/predict_live")
#def predict_live(txn: Transaction, user=Depends(verify_token)):
def predict_live(txn: Transaction, request: Request, user=Depends(verify_token)):
    try:
        ip_address = request.client.host
        user_agent = request.headers.get("user-agent")
        print("User IP:", ip_address)
        print("Device:", user_agent)
        
        import pandas as pd
        from predict import predict_fraud

        df = pd.DataFrame([txn.dict()])
        result_df = predict_fraud(df)

        row = result_df.iloc[0]

        return {
            "prediction": "Fraud" if int(row["fraud_prediction"]) == 1 else "Legit",
            "probability": float(row["fraud_probability"]),
            "risk_level": str(row["risk_level"]),
            "reasons": list(row["reasons"]) if isinstance(row["reasons"], list) else [],
            "ip_address": ip_address,
            "device": user_agent
        }
        #ip = request.client.host


    except Exception as e:
        return {"error": str(e)}

