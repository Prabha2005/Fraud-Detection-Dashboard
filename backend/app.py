from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from functools import lru_cache
import pandas as pd
import joblib
import os

from auth import create_token, verify_token, hash_password, verify_password
from database import get_db, create_table
from models import Transaction, LoginRequest


create_table()


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
# Signup Endpoint
# ----------------------------


@app.post("/signup")
def signup(data: LoginRequest):
    conn = get_db()

    hashed = hash_password(data.password)

    try:
        conn.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (data.username, hashed)
        )
        conn.commit()
        return {"message": "User created"}
    except:
        raise HTTPException(status_code=400, detail="User already exists")

# ----------------------------
# Authentication Endpoint
# ----------------------------

@app.post("/login")
def login(data: LoginRequest):
    conn = get_db()

    user = conn.execute(
        "SELECT * FROM users WHERE username = ?",
        (data.username,)
    ).fetchone()

    # ✅ FIX HERE
    if user and verify_password(data.password, user["password"]):
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
    



# ----------------------------
# Live Prediction Endpoint
# ----------------------------
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

