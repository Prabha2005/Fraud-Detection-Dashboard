import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt
import tempfile
import time
import random

# ----------------------------
# PAGE CONFIG (MUST BE FIRST)
# ----------------------------
st.set_page_config(page_title="UPI Fraud Detection", layout="wide")

# ----------------------------
# SIDEBAR NAVIGATION
# ----------------------------
page = st.sidebar.selectbox("Navigation", ["Dashboard", "About"])

# ----------------------------
# STYLING
# ----------------------------
st.markdown("""
<style>
[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #0f172a, #1e293b);
    color: #f1f5f9;
}
.card {
    background: rgba(255, 255, 255, 0.08);
    padding: 20px;
    border-radius: 20px;
    text-align: center;
}
.title {
    font-size: 38px;
    font-weight: 700;
    text-align: center;
    color: #38bdf8;
}
.subtitle {
    text-align: center;
    color: #94a3b8;
}
.fraud { color: #ef4444; }
.legit { color: #22c55e; }
</style>
""", unsafe_allow_html=True)

# ----------------------------
# HEADER
# ----------------------------
st.markdown('<div class="title">💳 Smart Fraud Detection Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Real-Time • Explainable • Intelligent Monitoring</div>', unsafe_allow_html=True)

API_URL = "https://fraud-detection-dashboard-c7ur.onrender.com/predict"

# ============================
# ABOUT PAGE
# ============================
if page == "About":

    st.title("📘 About Smart Fraud Detection Dashboard")

    st.markdown("""
    ### 💡 What is this App?
    AI-powered system to detect fraudulent UPI transactions.

    ### ⚙️ How it Works
    - Upload CSV → Bulk detection  
    - Real-time → Instant prediction  
    - Simulation → Continuous monitoring  

    ### 🧠 Features
    - Fraud probability scoring  
    - Risk classification  
    - Explainable AI  

    ### 🔐 Why it matters?
    Helps prevent financial fraud.
    """)

# ============================
# DASHBOARD
# ============================
elif page == "Dashboard":

    tab1, tab2, tab3 = st.tabs([
        "📁 Upload Transactions",
        "⚡ Real-Time Check",
        "🔄 Live Simulation"
    ])

    # ----------------------------
    # TAB 1: UPLOAD
    # ----------------------------
    with tab1:

        st.subheader("Upload Transaction CSV")
        csv_file = st.file_uploader("Choose CSV file", type=["csv"])

        if csv_file:

            with st.spinner("Processing..."):
                files = {"file": (csv_file.name, csv_file.getvalue(), "text/csv")}
                response = requests.post(API_URL, files=files)

            if response.status_code == 200:
                df = pd.DataFrame(response.json())

                st.success("Prediction completed ✅")
                st.dataframe(df)

                st.download_button(
                    "⬇ Download Results",
                    df.to_csv(index=False),
                    file_name="results.csv"
                )

            else:
                st.error(response.text)

    # ----------------------------
    # TAB 2: REAL-TIME
    # ----------------------------
    with tab2:

        st.subheader("Real-Time Check")

        amount = st.number_input("Amount")
        device = st.selectbox("Device Changed?", [0, 1])
        merchant = st.slider("Merchant Risk", 0.0, 1.0)
        geo = st.number_input("Geo Velocity")
        hour = st.slider("Hour", 0, 23)

        if st.button("Check Fraud"):

            payload = {
                "transaction_amount": amount,
                "device_change": device,
                "merchant_risk": merchant,
                "geo_velocity": geo,
                "hour_of_day": hour
            }

            res = requests.post(
                "https://fraud-detection-dashboard-c7ur.onrender.com/predict_live",
                json=payload
            )

            if res.status_code == 200:
                result = res.json()

                st.write(result)

                df = pd.DataFrame([result])
                st.download_button(
                    "⬇ Download Result",
                    df.to_csv(index=False),
                    file_name="realtime.csv"
                )

    # ----------------------------
    # TAB 3: SIMULATION
    # ----------------------------
    with tab3:

        st.subheader("Live Simulation")

        if st.button("Start Simulation"):

            results = []

            for i in range(5):

                payload = {
                    "transaction_amount": random.randint(100, 100000),
                    "device_change": random.choice([0, 1]),
                    "merchant_risk": round(random.random(), 2),
                    "geo_velocity": round(random.random() * 200, 2),
                    "hour_of_day": random.randint(0, 23)
                }

                res = requests.post(
                    "https://fraud-detection-dashboard-c7ur.onrender.com/predict_live",
                    json=payload
                )

                if res.status_code == 200:
                    result = res.json()
                    results.append(result)

                    st.write(result)

                time.sleep(1)

            df = pd.DataFrame(results)

            st.download_button(
                "⬇ Download Simulation",
                df.to_csv(index=False),
                file_name="simulation.csv"
            )

# ============================
# AI ASSISTANT
# ============================
st.sidebar.markdown("## 🤖 AI Assistant")

q = st.sidebar.selectbox("Ask something:", [
    "How this app works?",
    "What do I do now?",
    "What is fraud detection?"
])

if q == "How this app works?":
    st.sidebar.info("Uses ML to detect fraud.")
elif q == "What do I do now?":
    st.sidebar.info("Upload CSV or use real-time check.")
elif q == "What is fraud detection?":
    st.sidebar.info("Identifying suspicious transactions.")
