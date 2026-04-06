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
        st.subheader("Upload Transaction CSV (Prediction)")
        csv_file = st.file_uploader("Choose CSV file", type=["csv"])

        if csv_file:

            with st.spinner("Processing..."):
                files = {"file": (csv_file.name, csv_file.getvalue(), "text/csv")}
                response = requests.post(API_URL, files=files)

            if response.status_code == 200:

                df = pd.DataFrame(response.json())

                st.success("Prediction completed ✅")
                st.dataframe(df, use_container_width=True)

                total = len(df)
                fraud_count = (df["prediction"] == "Fraud").sum()

                col1, col2, col3 = st.columns(3)

                col1.markdown(f"<div class='card'><h4>Total</h4><h1>{total}</h1></div>", unsafe_allow_html=True)
                col2.markdown(f"<div class='card fraud'><h4>Fraud</h4><h1>{fraud_count}</h1></div>", unsafe_allow_html=True)
                col3.markdown(f"<div class='card legit'><h4>Legit</h4><h1>{total - fraud_count}</h1></div>", unsafe_allow_html=True)

                fig1, ax1 = plt.subplots()
                ax1.hist(df["probability"], bins=20)
                ax1.axvline(x=0.5, linestyle="--")
                st.pyplot(fig1)

                counts = df["prediction"].value_counts()
                fig2, ax2 = plt.subplots()
                ax2.bar(["Legit", "Fraud"], [counts.get("Legit", 0), counts.get("Fraud", 0)])
                st.pyplot(fig2)

                st.subheader("🧠 Fraud Analysis")
                st.dataframe(df[["prediction", "reasons"]])

                st.download_button(
                    "⬇ Download Results",
                    df.to_csv(index=False),
                    file_name="fraud_results.csv"
                )

            else:
                st.error(response.text)

    # ----------------------------
    # TAB 2: REAL-TIME
    # ----------------------------
    with tab2:

        st.subheader("⚡ Real-Time Transaction Check")

        amount = st.number_input("Transaction Amount", min_value=0.0)
        device = st.selectbox("Device Changed?", [0, 1])
        merchant = st.slider("Merchant Risk", 0.0, 1.0)
        geo = st.number_input("Geo Velocity", min_value=0.0)
        hour = st.slider("Hour of Day", 0, 23)

        if st.button("Check Fraud"):

            payload = {
                "transaction_amount": amount,
                "device_change": device,
                "merchant_risk": merchant,
                "geo_velocity": geo,
                "hour_of_day": hour
            }

            response = requests.post(
                "https://fraud-detection-dashboard-c7ur.onrender.com/predict_live",
                json=payload
            )

            if response.status_code == 200:

                result = response.json()
                df = pd.DataFrame([result])

                col1, col2, col3 = st.columns(3)

                col1.metric("Prediction", result["prediction"])
                col2.metric("Probability", round(result["probability"], 3))
                col3.metric("Risk Level", result["risk_level"])

                if result["prediction"] == "Fraud":
                    st.error(f"🚨 {result['reasons']}")
                else:
                    st.success("✅ Safe Transaction")

                fig, ax = plt.subplots()
                ax.bar(["Risk"], [result["probability"]])
                ax.set_ylim(0, 1)
                ax.set_title("Fraud Probability")
                st.pyplot(fig)

                st.download_button(
                    "⬇ Download Result",
                    df.to_csv(index=False),
                    file_name="realtime_result.csv"
                )

            else:
                st.error(response.text)

    # ----------------------------
    # TAB 3: SIMULATION
    # ----------------------------
    with tab3:

        st.subheader("🔄 Live Monitoring Dashboard")

        if st.button("Start Simulation"):

            results = []
            trend = []

            for i in range(10):

                payload = {
                    "transaction_amount": random.randint(100, 100000),
                    "device_change": random.choice([0, 1]),
                    "merchant_risk": round(random.random(), 2),
                    "geo_velocity": round(random.random() * 200, 2),
                    "hour_of_day": random.randint(0, 23)
                }

                response = requests.post(
                    "https://fraud-detection-dashboard-c7ur.onrender.com/predict_live",
                    json=payload
                )

                if response.status_code == 200:

                    result = response.json()
                    results.append(result)
                    trend.append(result["probability"])

                    st.write(f"### Transaction {i+1}")
                    st.write(payload)

                    if result["prediction"] == "Fraud":
                        st.error("🚨 Fraud Detected")
                    else:
                        st.success("✅ Legit")

                    fig, ax = plt.subplots()
                    ax.plot(trend)
                    ax.set_ylim(0, 1)
                    ax.set_title("Fraud Risk Trend")
                    st.pyplot(fig)

                else:
                    st.error(response.text)

                time.sleep(1)

            if results:
                df = pd.DataFrame(results)

                st.download_button(
                    "⬇ Download Simulation Results",
                    df.to_csv(index=False),
                    file_name="simulation_results.csv"
                )

# ============================
# AI ASSISTANT (UNCHANGED)
# ============================
st.sidebar.markdown("## 🤖 AI Assistant")

q = st.sidebar.selectbox("Ask something:", [
    "How this app works?",
    "What do I do now?",
    "What is fraud detection?",
    "How to use upload feature?"
])

if q == "How this app works?":
    st.sidebar.info("This app uses machine learning to detect fraud from transaction data.")
elif q == "What do I do now?":
    st.sidebar.info("Upload a CSV file or use real-time check to analyze transactions.")
elif q == "What is fraud detection?":
    st.sidebar.info("Fraud detection identifies suspicious transactions using patterns and AI models.")
elif q == "How to use upload feature?":
    st.sidebar.info("Go to Upload tab → Upload CSV → View results and download.")
else:
    st.sidebar.info("Please select a valid question.")

