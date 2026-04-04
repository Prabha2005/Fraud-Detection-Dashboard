import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt
import tempfile


st.markdown("""
<style>

/* MAIN BACKGROUND (smooth gradient) */
[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #0f172a, #1e293b);
    color: #f1f5f9;
}

/* CONTENT AREA (glass effect) */
[data-testid="stVerticalBlock"] {
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(12px);
    padding: 25px;
    border-radius: 18px;
    border: 1px solid rgba(255,255,255,0.1);
}

/* CARD STYLE (modern glass card) */
.card {
    background: rgba(255, 255, 255, 0.08);
    padding: 20px;
    border-radius: 20px;
    box-shadow: 0px 8px 30px rgba(0,0,0,0.4);
    text-align: center;
    transition: all 0.3s ease;
}
.card:hover {
    transform: translateY(-6px) scale(1.02);
    box-shadow: 0px 12px 40px rgba(0,0,0,0.6);
}

/* TITLE */
.title {
    font-size: 38px;
    font-weight: 700;
    text-align: center;
    background: linear-gradient(90deg, #38bdf8, #6366f1);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

/* SUBTITLE */
.subtitle {
    text-align: center;
    color: #94a3b8;
    font-size: 16px;
}

/* FRAUD */
.fraud {
    color: #ef4444;
    font-weight: bold;
}

/* LEGIT */
.legit {
    color: #22c55e;
    font-weight: bold;
}

/* BUTTON STYLE */
button[kind="primary"] {
    background: linear-gradient(90deg, #6366f1, #38bdf8);
    border: none;
    border-radius: 10px;
    padding: 10px 18px;
    font-weight: 600;
    transition: 0.3s;
}
button[kind="primary"]:hover {
    opacity: 0.9;
    transform: scale(1.05);
}

/* TABS */
button[data-baseweb="tab"] {
    font-size: 15px;
    padding: 10px;
    border-radius: 8px;
}

/* FILE UPLOADER */
[data-testid="stFileUploader"] {
    background: rgba(255,255,255,0.08);
    border-radius: 12px;
    padding: 12px;
    border: 1px dashed #475569;
}

/* REMOVE HEADER */
header {
    background: transparent !important;
}

</style>
""", unsafe_allow_html=True)
# ----------------------------
# PAGE CONFIG
# ----------------------------
st.set_page_config(page_title="UPI Fraud Detection", layout="wide")

st.markdown('<div class="title">💳 Smart Fraud Detection Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Real-Time • Explainable • Intelligent Monitoring</div>', unsafe_allow_html=True)

API_URL = "http://127.0.0.1:8000/predict"

# ----------------------------
# DOWNLOAD HELPER
# ----------------------------
def create_download_file(content):
    file = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
    file.write(content.encode())
    file.close()
    return file.name

# ----------------------------
# TABS
# ----------------------------
tab1, tab2, tab3 = st.tabs([
    "📁 Upload Transactions",
    "⚡ Real-Time Check",
    "🔄 Live Simulation"
])

# ============================
# TAB 1: CSV Upload
# ============================
with tab1:

    st.subheader("Upload Transaction CSV (Prediction)")
    csv_file = st.file_uploader("Choose CSV file", type=["csv"])

    if csv_file is not None:

        with st.spinner("Processing..."):
            files = {"file": (csv_file.name, csv_file.getvalue(), "text/csv")}
            response = requests.post(API_URL, files=files)

        if response.status_code == 200:
            df = pd.DataFrame(response.json())
            latest_upload_df = df

            st.success("Prediction completed ✅")
            st.dataframe(df, use_container_width=True)

            total = len(df)
            fraud_count = (df["prediction"] == "Fraud").sum()

            col1, col2, col3 = st.columns(3)

            col1.markdown(f"<div class='card'><h4>Total</h4><h1>{total}</h1></div>", unsafe_allow_html=True)
            col2.markdown(f"<div class='card'><h4 class='fraud'>Fraud</h4><h1 class='fraud'>{fraud_count}</h1></div>", unsafe_allow_html=True)
            col3.markdown(f"<div class='card'><h4 class='legit'>Legit</h4><h1 class='legit'>{total - fraud_count}</h1></div>", unsafe_allow_html=True)

            # Charts
            fig1, ax1 = plt.subplots()
            ax1.hist(df["probability"], bins=20)
            ax1.axvline(x=0.5, linestyle="--")
            st.pyplot(fig1)

            counts = df["prediction"].value_counts()
            fig2, ax2 = plt.subplots()
            ax2.bar(["Legit", "Fraud"], [counts.get("Legit", 0), counts.get("Fraud", 0)])
            st.pyplot(fig2)

            st.subheader("🧠 Fraud Analysis")
            st.write(df[["prediction", "reasons"]])

            # Download
            st.download_button(
                "⬇ Download Results",
                df.to_csv(index=False),
                file_name="fraud_results.csv"
            )

        else:
            st.error(response.text)

# ============================
# TAB 2: REAL-TIME
# ============================
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

        response = requests.post("http://127.0.0.1:8000/predict_live", json=payload)

        if response.status_code == 200:
            result = response.json()
            # Convert single result to DataFrame
            latest_realtime_df = pd.DataFrame([result])

            
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
            st.pyplot(fig)

            if latest_realtime_df is not None:
                st.download_button(
        "⬇ Download Result",
        latest_realtime_df.to_csv(index=False),
        file_name="realtime_result.csv"
    )
        else:
            st.error("Error in prediction")

# ============================
# TAB 3: SIMULATION
# ============================
with tab3:

    st.subheader("🔄 Live Monitoring Dashboard")

    import time, random

    if st.button("Start Simulation"):

        results_list = []
        simulation_results = []

        for i in range(10):

            payload = {
                "transaction_amount": random.randint(100, 100000),
                "device_change": random.choice([0, 1]),
                "merchant_risk": round(random.random(), 2),
                "geo_velocity": round(random.random() * 200, 2),
                "hour_of_day": random.randint(0, 23)
            }

            response = requests.post("http://127.0.0.1:8000/predict_live", json=payload)

            if response.status_code == 200:
                result = response.json()

                # ✅ store results AFTER getting response
                simulation_results.append(result)
                results_list.append(result["probability"])

                st.write(f"### Transaction {i+1}")
                st.write(payload)

                if result["prediction"] == "Fraud":
                    st.error("🚨 Fraud Detected")
                else:
                    st.success("✅ Legit")

                # Graph
                fig, ax = plt.subplots()
                ax.plot(results_list)
                ax.set_ylim(0, 1)
                ax.set_title("Fraud Risk Trend")
                st.pyplot(fig)

            else:
                st.error(response.text)

            time.sleep(1)

        # ✅ AFTER LOOP (important)
        if simulation_results:
            latest_simulation_df = pd.DataFrame(simulation_results)

            st.download_button(
                "⬇ Download Simulation Results",
                latest_simulation_df.to_csv(index=False),
                file_name="simulation_results.csv"
            )