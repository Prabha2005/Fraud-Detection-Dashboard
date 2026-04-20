from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from functools import lru_cache
import pandas as pd
import joblib
import os
import tempfile
import re
import pdfplumber
import random

from auth import create_token, verify_token, hash_password, verify_password
from database import create_transaction_table, get_db, create_table
from models import Transaction, LoginRequest

from shap_utils import explain_prediction
from velocity_features import get_velocity_features   # ✅ IMPORTANT
from audit_logger import log_prediction
from retrain import retrain_model

# Load SHAP explainer
try:
    shap_explainer = joblib.load("model/shap_explainer.pkl")
except:
    shap_explainer = None

create_table()
create_transaction_table()

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
# Feature Order
# ----------------------------
FEATURE_ORDER = [
    "transaction_amount",
    "device_change",
    "merchant_risk",
    "geo_velocity",
    "hour_of_day",
    "txn_count_24h",
    "amount_zscore",
    "amount_vs_max",
    "amount_sum_24h"
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
        # 🔥 Add missing velocity features (default values for CSV)
        df["txn_count_24h"] = 0
        df["amount_zscore"] = 0
        df["amount_vs_max"] = 1
        df["amount_sum_24h"] = 0

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
def predict_live(txn: Transaction, request: Request, user=Depends(verify_token)):
    try:
        ip_address = request.client.host
        user_agent = request.headers.get("user-agent")

        import pandas as pd
        from predict import predict_fraud

        #df = pd.DataFrame([txn.dict()])
        data = txn.dict()
        # ✅ Map API fields → ML fields
        data["transaction_amount"] = data.get("amount")
        data["geo_velocity"] = data.get("location")  # or better: separate field later
        data["hour_of_day"] = data.get("time")

        data["device_change"] = data.get("device_change", 0)
        data["merchant_risk"] = data.get("merchant_risk", 0)


        #df = pd.DataFrame([data])
        #explanation = explain_prediction(shap_explainer, df)
        

        # ----------------------------
        # BEHAVIOR TRACKING
        # ----------------------------
        conn = get_db()
        username = user.get("user")

        velocity = get_velocity_features(username, txn.amount, conn)
        # Merge
        data.update(velocity)
        df = pd.DataFrame([data])
        # ✅ Enforce feature order
        df = df[FEATURE_ORDER]
        result_df = predict_fraud(df)
        row = result_df.iloc[0]
        # ✅ SHAP explanation
        #explanation = explain_prediction(shap_explainer, df)
        # ✅ Safe SHAP call
        if shap_explainer:
            explanation = explain_prediction(shap_explainer, pd.DataFrame([row]))
         else:
            if row["reasons"]:   # ✅ only if reasons exist
                    explanation = {
            "top_reasons": row["reasons"]
        }
            else:
                explanation = None


        history = conn.execute(
            "SELECT amount FROM transactions WHERE username = ? ORDER BY id DESC LIMIT 5",
            (username,)
        ).fetchall()

        avg_amount = 0
        if history:
            avg_amount = sum([row["amount"] for row in history]) / len(history)

        behavior_flag = ""

        if avg_amount > 0 and txn.amount > 3 * avg_amount:
            behavior_flag = "Unusual high transaction compared to history"

        # ----------------------------
        # STORE TRANSACTION
        # ----------------------------
        conn.execute(
            "INSERT INTO transactions (username, amount, ip, device) VALUES (?, ?, ?, ?)",
            (username, txn.amount, ip_address, user_agent)
        )
        conn.commit()

        log_prediction({
    "user": username,
    "amount": txn.amount,
    "prediction": "Fraud" if int(row["fraud_prediction"]) == 1 else "Legit",
    "probability": float(row["fraud_probability"]),
    "ip": ip_address
})

        # ----------------------------
        # RESPONSE
        # ----------------------------
        return {
            "prediction": "Fraud" if int(row["fraud_prediction"]) == 1 else "Legit",
            "probability": float(row["fraud_probability"]),
            "risk_level": str(row["risk_level"]),
            "reasons": list(row["reasons"]) if isinstance(row["reasons"], list) else [],
            "behavior_flag": behavior_flag,
            "ip_address": ip_address,
            "device": user_agent,
            "explanation": explanation
        }

    except Exception as e:
        return {"error": str(e)}
    
# ----------------------------
# PDF Upload Endpoint
# ----------------------------
@app.post("/predict_pdf")
async def predict_pdf(file: UploadFile = File(...), user=Depends(verify_token)):

    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files allowed")

    try:
        # ----------------------------
        # SAVE TEMP FILE
        # ----------------------------
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(await file.read())
            temp_path = tmp.name

        # ----------------------------
        # PARSE PDF (GPay)
        # ----------------------------
        with pdfplumber.open(temp_path) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        # ----------------------------
        # EXTRACT TRANSACTIONS
        # ----------------------------
        import re, random
        lines = text.split("\n")

        transactions = []
        seen_users = set()
        current_merchant = None

        for line in lines:
            line = line.strip()

            name_match = re.search(r"(Paid to|Received from)\s+(.+)", line)
   
            if name_match:
                current_merchant = name_match.group(2).strip()
                print("FOUND MERCHANT:", current_merchant)
                continue
            
            amount_match = re.search(r"₹\s?([\d,]+\.?\d*)", line)

            if amount_match:
                amount = float(amount_match.group(1).replace(",", ""))

                merchant = current_merchant if current_merchant else "Unknown"

                # New payee detection
                is_new = 1 if merchant not in seen_users else 0
                seen_users.add(merchant)
                
                transactions.append({
        "transaction_amount": amount,
        "merchant": merchant,   # ✅ 
            "new_payee": is_new,    # ✅ IMPORTANT
        "device_change": 0,
        "merchant_risk": round(random.random(), 2),
        "geo_velocity": round(random.random() * 200, 2),
        "hour_of_day": random.randint(0, 23)
    })
            

        # ✅ MUST BE INSIDE try
        if not transactions:
            raise HTTPException(status_code=400, detail="No transactions found in PDF")

        df = pd.DataFrame(transactions)
        # Add missing velocity features (default for PDF)
        df["txn_count_24h"] = 0
        df["amount_zscore"] = 0
        df["amount_vs_max"] = 1
        df["amount_sum_24h"] = 0
        # Enforce feature order
        df = df[FEATURE_ORDER]

        # 
        

        
        
        # ----------------------------
        # PREDICT
        # ----------------------------
        from predict import predict_fraud

        result_df = predict_fraud(df)

        response = []
        for _, row in result_df.iterrows():
            amount = float(row["transaction_amount"])
            prediction = "Fraud" if row["fraud_prediction"] == 1 else "Legit"
            probability = round(row["fraud_probability"], 3)

            # 🔥 RULE FIX
            if amount < 50:
                prediction = "Legit"
                probability = 0.001

            
            # SHAP explanation
            if shap_explainer:
                explanation = explain_prediction(shap_explainer, pd.DataFrame([row]))
            else:
                if row["reasons"]:   # ✅ only if reasons exist
                    explanation = {
            "top_reasons": row["reasons"]
        }
                else:
                    explanation = None
                

    # Audit logging
            log_prediction({
    "user": user.get("user"),
    "amount": amount,
    "prediction": prediction,
    "probability": probability,
    "source": "pdf"
})
            
        
            response.append({
        "amount": amount,
        "new_payee": row.get("new_payee", 0),
        "prediction": prediction,
        "probability": probability,
        "risk_level": row["risk_level"],
        "reasons": row["reasons"],
        "explanation": explanation
    })

        return response

    except Exception as e:
        return {"error": str(e)}
    
# ----------------------------
# Retrain Endpoint
# ----------------------------
@app.post("/retrain")
def retrain():
    return retrain_model()
