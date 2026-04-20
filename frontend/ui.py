import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt
import tempfile
import time
import random
from streamlit_cookies_manager import EncryptedCookieManager


#API_URL = "http://127.0.0.1:8000"
API_URL = "https://fraud-detection-dashboard-c7ur.onrender.com"

cookies = EncryptedCookieManager(
    prefix="fraud_app",
    password="some_secret_key"
)

if not cookies.ready():
    st.stop()


#st.session_state.token = token

if "token" not in st.session_state:
    st.session_state.token = cookies.get("token")

st.set_page_config(page_title="UPI Fraud Detection", layout="wide")

# ----------------------------
# AUTHENTICATION (FINAL CLEAN)
# ----------------------------
if st.session_state.token is None:

    st.markdown('<div class="title">🔐 UPI Fraud Detection System</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Secure Login / Signup</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1,2,1])

    with col2:
        mode = st.radio("Select", ["Login", "Signup"], horizontal=True)

        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if mode == "Signup":
            if st.button("Create Account", use_container_width=True):
                res = requests.post(
                    f"{API_URL}/signup",
                    json={"username": username, "password": password}
                )
                if res.status_code == 200:
                    st.success("Account created ✅")
                else:
                    st.error("User already exists ❌")

        else:
            if st.button("Login", use_container_width=True):
                response = requests.post(
                    f"{API_URL}/login",
                    json={"username": username, "password": password}
                )

                if response.status_code == 200:
                    token = response.json()["token"]
                    # ✅ Save in session
                    st.session_state.token = token
                    # ✅ Save in cookie
                    cookies["token"] = token
                    cookies.save()
                    st.success("Login successful ✅")
                    st.rerun()
                else:
                    st.error("Invalid credentials ❌")

    st.stop()


# Logout button
#st.sidebar.button("Logout", on_click=lambda: st.session_state.update({"token": None}))
if st.button("Logout"):
    cookies["token"] = ""
    cookies.save()
    st.session_state.token = None
    st.rerun()

# ----------------------------
# PAGE CONFIG (MUST BE FIRST)
# ----------------------------
#st.set_page_config(page_title="UPI Fraud Detection", layout="wide")

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

#API_URL = "https://fraud-detection-dashboard-c7ur.onrender.com/predict"


# ============================
# ABOUT PAGE
# ============================
if page == "About":

    st.title("📘 About Smart Fraud Detection Dashboard")

    st.markdown("""
    ## 💡 What is this App?
    This is an **AI-powered UPI Fraud Detection Dashboard** that analyzes transaction data and identifies **potentially suspicious transactions**.

    The system supports both **real-time detection** and **bulk analysis**, making it useful for understanding fraud patterns.

    ---

    ## 💳 What is UPI?
    UPI (Unified Payments Interface) allows instant money transfer using apps like:
    • Google Pay  
    • PhonePe  
    • Paytm  

    While it is fast and convenient, it is also vulnerable to fraud.

    ---

    ## ⚙️ How this App Works

    🔹 **CSV Upload (Bulk Detection)**  
    Upload transaction data → analyze multiple transactions  

    🔹 **Real-Time Mode**  
    Enter transaction → instant fraud prediction  

    🔹 **Live Simulation**  
    Simulates real-world transactions and trends  

    🔹 **PDF Analysis**  
    Upload Google Pay PDF → extract transactions → detect fraud  

    ---
    """)

    st.info("💡 This system uses Machine Learning + basic behavior analysis for fraud detection.")

    # ----------------------------
    # ARCHITECTURE
    # ----------------------------
    st.markdown("## 🧠 System Architecture")
    st.image("frontend/images/1st-image.jpg", caption="How the app works", use_container_width=True)

    st.markdown("""
    This system follows a **3-layer architecture**:

    1️⃣ **Frontend (Streamlit UI)**  
    - User input and visualization  

    2️⃣ **Backend (FastAPI)**  
    - API handling and authentication (JWT)  

    3️⃣ **Machine Learning Model (XGBoost)**  
    - Predicts fraud probability  

    📊 Data flows from user → API → model → result → dashboard
    """)

    # ----------------------------
    # WORKFLOW
    # ----------------------------
    st.markdown("## 🔄 System Workflow")
    st.image("frontend/images/2nd-image.jpg", caption="System Workflow", use_container_width=True)

    st.markdown("""
    ### Step-by-Step Flow:

    1️⃣ User inputs data / uploads file  
    2️⃣ Data sent to backend  
    3️⃣ Features prepared (amount + simulated behavior)  
    4️⃣ ML model predicts fraud probability  
    5️⃣ Risk level assigned  
    6️⃣ Results displayed  

    🎯 Output: Fraud / Legit + Risk Level + Reasons
    """)

    # ----------------------------
    # FEATURES
    # ----------------------------
    st.markdown("""
    ## 🧠 Key Features

    ✔ AI-based fraud detection  
    ✔ Real-time transaction analysis  
    ✔ Bulk transaction processing  
    ✔ Basic behavior-based detection  
    ✔ Risk level classification  
    ✔ Explainable results (reasons)  
    ✔ Interactive dashboard  

    ---
    """)

    # ----------------------------
    # PERFORMANCE
    # ----------------------------
    st.markdown("## 📊 Model Performance")

    st.markdown("""
    ✔ Accuracy: ~93%  
    ✔ Recall: 0.93  
    ✔ Balanced detection performance  

    ⚠️ Note: Some features like geo velocity and merchant risk are simulated for demonstration.
    """)

    # Graph
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots()
    ax.bar(["Accuracy", "Recall", "Precision"], [0.933, 0.93, 0.91])
    ax.set_ylim(0, 1)
    ax.set_title("Model Performance Metrics")
    st.pyplot(fig)

    # ----------------------------
    # EXAMPLE
    # ----------------------------
    st.markdown("""
    ## 🔍 Example

    If a user normally sends ₹500 and suddenly sends ₹50,000  
    👉 The system flags it as suspicious  

    ---
    """)

    # ----------------------------
    # NOTE
    # ----------------------------
    st.markdown("""
    ## ⚠️ Important Note

    • This is a prototype system  
    • Some behavioral features are simulated  
    • Designed for learning and demonstration purposes  

    ---
    """)

    # ----------------------------
    # GOAL
    # ----------------------------
    st.markdown("""
    ## 🚀 Project Goal

    To build a **smart fraud detection system prototype**  
    using AI and data analysis for fintech applications.
    """)

# ============================
# DASHBOARD
# ============================
elif page == "Dashboard":

    tab1, tab2, tab3, tab4 = st.tabs([
        "📁 Upload Transactions",
        "⚡ Real-Time Check",
        "🔄 Live Simulation",
        "📄 Upload GPay PDF"
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

                response = requests.post(
    f"{API_URL}/predict",
    files=files,
    headers={"Authorization": f"Bearer {st.session_state.token}"}
)
                #response = requests.post(API_URL, files=files)

            if response.status_code == 200:

                #df = pd.DataFrame(response.json())
                data = response.json()
                # ✅ Handle error response
                if isinstance(data, dict) and "error" in data:
                    st.error(f"Backend Error: {data['error']}")
                    st.stop()
                # ✅ Normal case
                df = pd.DataFrame(data)

                st.success("Prediction completed ✅")

                # CALCULATIONS (FIRST) 
                # ----------------------------
                total = len(df)
                fraud_count = (df["prediction"] == "Fraud").sum()
                high_risk = (df["probability"] > 0.8).sum()
                medium_risk = ((df["probability"] > 0.5) & (df["probability"] <= 0.8)).sum()

                # ----------------------------
                # SUMMARY CARDS
                # ----------------------------
                col1, col2, col3 = st.columns(3)

                col1.markdown(f"<div class='card'><h4>Total</h4><h1>{total}</h1></div>", unsafe_allow_html=True)
                col2.markdown(f"<div class='card fraud'><h4>Fraud</h4><h1>{fraud_count}</h1></div>", unsafe_allow_html=True)
                col3.markdown(f"<div class='card legit'><h4>Legit</h4><h1>{total - fraud_count}</h1></div>", unsafe_allow_html=True)

                # ----------------------------
                # ALERT
                # ----------------------------
                if fraud_count > 0:
                    st.warning(f"⚠️ {fraud_count} potentially fraudulent transactions detected!")
                else:
                    st.success("✅ No fraud detected")

                # ----------------------------
                # RISK SUMMARY
                # ----------------------------
                st.markdown("### 📊 Risk Summary")
                col1, col2 = st.columns(2)
                col1.metric("High Risk", high_risk)
                col2.metric("Medium Risk", medium_risk)

                # ----------------------------
                # TABLE (HIGHLIGHTED)
                # ----------------------------
                #st.dataframe(df, use_container_width=True)
                def highlight_fraud(row):
                     return ["background-color: #7f1d1d" if row["prediction"] == "Fraud" else "" for _ in row]
                st.dataframe(df.style.apply(highlight_fraud, axis=1), use_container_width=True)


                # ----------------------------
                # TOP FRAUDS + VISUALS
                # ----------------------------                
                st.subheader("🚨 Top Suspicious Transactions")
                top_fraud = df.sort_values(by="probability", ascending=False).head(5)
                st.dataframe(top_fraud)

                #----------------------------
                # CHARTS
                # ----------------------------
                fig1, ax1 = plt.subplots()
                ax1.hist(df["probability"], bins=20)
                ax1.axvline(x=0.5, linestyle="--")
                st.pyplot(fig1)

                counts = df["prediction"].value_counts()
                fig2, ax2 = plt.subplots()
                ax2.bar(["Legit", "Fraud"], [counts.get("Legit", 0), counts.get("Fraud", 0)])
                st.pyplot(fig2)

                #----------------------------
                # ANALYSIS
                # ----------------------------
                st.subheader("🧠 Fraud Analysis")
                #st.dataframe(df[["prediction", "reasons"]])
                st.dataframe(df[["prediction", "probability", "risk_level", "reasons"]])

                #----------------------------
                # DOWNLOAD
                # ----------------------------
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

        amount = st.number_input("💰 Transaction Amount", min_value=0.0)
        device = st.selectbox("📱 Device Changed?", [0, 1])
        merchant = st.slider("🏪 Merchant Risk", 0.0, 1.0)
        geo = st.number_input("🌍 Geo Velocity", min_value=0.0)
        hour = st.slider("⏰ Hour of Day", 0, 23)

        #if st.button("Check Fraud"):
        check = st.button("Check Fraud", use_container_width=True)
        if check:

            if amount <= 0:
                st.warning("⚠️ Enter valid transaction amount")
                st.stop()
            
            payload = {
    "amount": amount,           # ✅ correct variable
    "time": hour,               # ✅ correct variable
    "location": "India",            # ✅ mapped
    "device_change": device,
    "merchant_risk": merchant,
    "geo_velocity": geo
}

            #payload = {
            #    "transaction_amount": amount,
            #    "device_change": device,
            #    "merchant_risk": merchant,
            #    "geo_velocity": geo,
            #    "hour_of_day": hour
            #}

            

           # response = requests.post(
            #    "https://fraud-detection-dashboard-c7ur.onrender.com/predict_live",
             #   json=payload
            #)
            # ✅ Prepare headers safely
            headers = {}
            if st.session_state.token:
                headers = {"Authorization": f"Bearer {st.session_state.token}"}
            response = requests.post(
    f"{API_URL}/predict_live",
    json=payload,
    headers=headers
)
            if response.status_code == 200:

                result = response.json()
                # 🔥 Handle backend errors safely
                if isinstance(result, dict) and "error" in result:
                    st.error(f"Backend Error: {result['error']}")
                    st.stop()
                
                if isinstance(result, dict) and "detail" in result:
                    st.error(f"API Error: {result['detail']}")
                    st.stop()
                df = pd.DataFrame([result])

                col1, col2, col3 = st.columns(3)

                col1.metric("Prediction", result["prediction"])
                col2.metric("Probability", round(result["probability"], 3))
                col3.metric("Risk Level", result["risk_level"])

                st.markdown("### 🌐 Transaction Context")
                ctx1, ctx2 = st.columns(2)
                ctx1.write(f"IP Address: {result.get('ip_address')}")
                ctx2.write(f"Device: {result.get('device')}")

                if result.get("behavior_flag"):
                    st.markdown(f"""
    <div style="
        background-color:#1e293b;
        padding:12px;
        border-radius:10px;
        border-left:5px solid #facc15;
        color:#facc15;
        font-weight:600;
    ">
    ⚠️ {result['behavior_flag']}
    </div>
    """, unsafe_allow_html=True)

                if result["prediction"] == "Fraud":
                    #st.error(f"🚨 {result['reasons']}")
                    #st.error(f"🚨 {result['transaction_amount contributed']}, {result['merchant_risk contributed']}, {result['geo_velocity contributed']} were key factors.")
                    st.error("🚨 Fraud Detected!")
                    for reason in result["reasons"]:
                        st.write(f"• {reason}")
                        # 🔥 SHAP Explanation (NEW)
                    if result.get("explanation"):
                        st.markdown("### 🧠 AI Explanation")
                            
                        for reason in result["explanation"].get("top_reasons", []):
                            st.write(f"👉 {reason}")
                else:
                    st.success("✅ Safe Transaction")

                # 🔥 Risk message FIRST
                if result["probability"] > 0.8:
                    st.warning("🔥 High Risk Transaction")
                elif result["probability"] > 0.5:
                    st.info("⚠️ Medium Risk")
                else:
                    st.success("✅ Low Risk")

                # Charts    
                fig, ax = plt.subplots()
                #ax.bar(["Risk"], [result["probability"]])
                ax.bar(["Legit", "Fraud"], [1 - result["probability"], result["probability"]])
                ax.set_ylim(0, 1)
                #ax.set_title("Fraud Probability")
                ax.set_title("Fraud vs Legit Probability")
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

            chart_placeholder = st.empty()
            status_placeholder = st.empty()
            summary_placeholder = st.empty()

            fraud_count = 0

            st.info("🔄 Simulating real-time transaction monitoring...")

            for i in range(10):
                random_amount = random.randint(100, 100000)
                random_geo = round(random.random() * 200, 2)
                random_hour = random.randint(0, 23)
                random_device = random.choice([0, 1])
                random_merchant = round(random.random(), 2)
                
                payload = {
    # FastAPI fields
    "amount": random_amount,
    "time": random_hour,
    "location": str(random_geo),

    # ML fields
    "transaction_amount": random_amount,
    "geo_velocity": random_geo,
    "hour_of_day": random_hour,

    # common
    "device_change": random_device,
    "merchant_risk": random_merchant
}

                #response = requests.post(
                 #   "https://fraud-detection-dashboard-c7ur.onrender.com/predict_live",
                  #  json=payload
                #)
                response = requests.post(
    f"{API_URL}/predict_live",
    json=payload,
    headers={"Authorization": f"Bearer {st.session_state.token}"}
)
             

                if response.status_code == 200:
                    result = response.json()
                    
                    if "probability" not in result:
                        st.error(f"Unexpected API response: {result}")
                        continue
                    
                    results.append(result)
                    trend.append(result["probability"])

                    #st.write(f"### Transaction {i+1}") 
                    #st.write(payload)
                    if result["prediction"] == "Fraud":
                        fraud_count += 1

                    #if result["prediction"] == "Fraud":
                    #    st.error("🚨 Fraud Detected")
                    #else:
                    #    st.success("✅ Legit")

                    # ----------------------------
                    # LIVE STATUS (UPDATED)
                    # ----------------------------
                    with status_placeholder.container():
                        st.write(f"### Transaction {i+1}")
                        st.json(payload)

                        if result["prediction"] == "Fraud":
                            st.error("🚨 Fraud Detected")
                        else:
                            st.success("✅ Legit Transaction")

                        # Behavior flag
                        if result.get("behavior_flag"):
                            st.warning(f"⚠️ {result['behavior_flag']}")

                    # ----------------------------
                    # LIVE CHART (SMOOTHED)
                    # ----------------------------
                    with chart_placeholder.container():
                        fig, ax = plt.subplots()
                        ax.plot(trend, marker="o")
                        ax.set_ylim(0, 1)
                        ax.set_title("📈 Fraud Risk Trend (Live)")
                        st.pyplot(fig)

                    # ----------------------------
                    # SUMMARY DASHBOARD
                    # ----------------------------
                    with summary_placeholder.container():
                        total = len(trend)
                        st.markdown("### 📊 Live Summary")

                        col1, col2 = st.columns(2)
                        col1.metric("Total Transactions", total)
                        col2.metric("Fraud Detected", fraud_count)

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
    
    # ----------------------------
    # # TAB 4: PDF UPLOAD (NEW)
    # # ----------------------------
    with tab4:
        st.subheader("📄 Upload Google Pay PDF")
        pdf_file = st.file_uploader("Upload GPay PDF", type=["pdf"])
        if pdf_file:
            with st.spinner("Extracting transactions from PDF..."):
                files = {
                "file": (pdf_file.name, pdf_file.getvalue(), "application/pdf")
            }
                response = requests.post(
                f"{API_URL}/predict_pdf",   # 🔥 new endpoint
                files=files,
                headers={"Authorization": f"Bearer {st.session_state.token}"}
            )
            
            #if response.status_code == 200:
            #    df = pd.DataFrame(response.json())
            #    st.success("PDF processed successfully ✅")
            #    st.dataframe(df, use_container_width=True)

            if response.status_code == 200:
                data = response.json()
                st.write(data)

                # ✅ FIRST handle error
                if isinstance(data, dict) and "error" in data:
                    st.error(f"Backend Error: {data['error']}")
                    st.stop()
                # 🔍 DEBUG LINE (ADD HERE)
                # item in data:
                #    if isinstance(item, dict) and item.get("explanation"):
                #        st.markdown("### 🧠 AI Explanation")
                #        for reason in item["explanation"].get("top_reasons", []):
                #            st.write(f"👉 {reason}")

                
                # ✅ Handle error response
                if isinstance(data, dict) and "error" in data:
                    st.error(f"Backend Error: {data['error']}")
                    st.stop()

                df = pd.DataFrame(data)

                # Summary
                fraud_count = (df["prediction"] == "Fraud").sum()
                
                if fraud_count > 0:
                    st.warning(f"⚠️ {fraud_count} suspicious transactions detected!")
                else:
                    st.success("✅ No fraud detected")

                st.download_button(
                "⬇ Download Results",
                df.to_csv(index=False),
                file_name="pdf_results.csv"
            )

            else:
                st.error(response.text)


# ============================
# AI ASSISTANT (UNCHANGED)
# ============================
st.sidebar.markdown("## 🤖 AI Assistant")

# ----------------------------
# QUICK BUTTONS (NEW 🔥)
# ----------------------------
st.sidebar.markdown("### 💡 Quick Questions")

col1, col2 = st.sidebar.columns(2)

user_input = None  # IMPORTANT

if col1.button("What is fraud?"):
    user_input = "what is fraud"

if col2.button("What is phishing?"):
    user_input = "what is phishing"

if col1.button("How app works?"):
    user_input = "how this app works"

if col2.button("UPI info"):
    user_input = "what is upi"


# ----------------------------
# CHAT INPUT (NEW 💬)
# ----------------------------
chat_input = st.sidebar.chat_input("Ask anything...")

if chat_input:
    user_input = chat_input.lower()

# ----------------------------
# DROPDOWN (KEEP YOUR EXISTING)
# ----------------------------
q = st.sidebar.selectbox("Or select a question:", [
    "None",
    "How this app works?",
    "What do I do now?",
    "What is fraud detection?",
    "How to use upload feature?",
    "What is UPI and digital payment?",
    "What is phishing?",
    "How fraud happens in digital payments?",
    "How this system detects fraud?",
    "What should I do if fraud is detected?",
    "Is my data safe here?"
])

# If dropdown used
if q != "None":
    user_input = q.lower()

# ----------------------------
# RESPONSE LOGIC (YOUR EXISTING)
# ----------------------------
if user_input:

    if "how this app works" in user_input:
        st.sidebar.info("This app uses machine learning to detect fraud from transaction data.")

    elif "what do i do" in user_input:
        st.sidebar.info("Upload a CSV file or use real-time check to analyze transactions.")

    elif "fraud detection" in user_input:
        st.sidebar.info("Fraud detection identifies suspicious transactions using patterns and AI models.")

    elif "upload" in user_input:
        st.sidebar.info("Go to Upload tab → Upload CSV → View results and download.")

    elif "upi" in user_input:
        st.sidebar.info("""
UPI allows instant money transfer using apps like Google Pay or PhonePe.

It is fast but can be targeted by fraud if users are not careful.
""")

    elif "phishing" in user_input:
        st.sidebar.info("""
Phishing is when attackers trick you into sharing OTP or bank details.

❌ Never share OTP or PIN
""")

    elif "how fraud happens" in user_input:
        st.sidebar.info("""
Fraud happens when attackers:
• Steal OTP
• Use fake apps
• Access unknown devices
""")

    elif "detects fraud" in user_input:
        st.sidebar.info("""
This system uses AI + behavior analysis.

It checks:
• Amount
• Device
• Location
• Past behavior
""")

    elif "what should i do" in user_input:
        st.sidebar.info("""
1. Stop transaction
2. Contact bank
3. Change passwords
4. Report fraud
""")

    elif "safe" in user_input:
        st.sidebar.info("""
Yes, your data is secure.

Authentication is used and data is not shared.
""")

    else:
        st.sidebar.info("Try asking about fraud, phishing, UPI, or safety tips.")


# ----------------------------
# DROPDOWN RESPONSES (YOUR EXISTING)
# ----------------------------
if q == "How this app works?":
    st.sidebar.info("This app uses machine learning to detect fraud from transaction data.")
elif q == "What do I do now?":
    st.sidebar.info("Upload a CSV file or use real-time check to analyze transactions.")
elif q == "What is fraud detection?":
    st.sidebar.info("Fraud detection identifies suspicious transactions using patterns and AI models.")
elif q == "How to use upload feature?":
    st.sidebar.info("Go to Upload tab → Upload CSV → View results and download.")

elif q == "What is UPI and digital payment?":
    st.sidebar.info("""
UPI (Unified Payments Interface) is a system that allows you to send or receive money instantly using your mobile phone.

Examples:
• Sending money using Google Pay, PhonePe, Paytm
• Paying bills online

It is fast and easy, but because it is digital, it can also be targeted by fraudsters.
""")

elif q == "What is phishing?":
    st.sidebar.info("""
Phishing is a type of fraud where attackers try to trick you into sharing your personal information.

Examples:
• Fake messages asking for OTP
• Fake bank links
• Calls pretending to be bank officials

Always remember:
❌ Never share OTP or PIN with anyone
""")

elif q == "How fraud happens in digital payments?":
    st.sidebar.info("""
Fraud can happen in many ways:

• Someone steals your OTP
• Fake apps or websites
• Sudden large transactions from your account
• Unknown device access

Fraud usually happens when something unusual occurs in your normal behavior.
""")

elif q == "How this system detects fraud?":
    st.sidebar.info("""
This system uses Artificial Intelligence (AI) to detect fraud.

It checks:
• Transaction amount
• Device changes
• Location differences
• Merchant risk

It also compares your past behavior:
👉 If something unusual happens → it flags as fraud

Example:
If you usually send ₹500 and suddenly send ₹50,000 → suspicious
""")
    
elif q == "What should I do if fraud is detected?":
    st.sidebar.info("""
If a transaction is marked as fraud:

1. Stop the transaction immediately
2. Contact your bank
3. Change your passwords and PIN
4. Check recent transactions
5. Report to cybercrime portal

Act fast to prevent loss.
""")
    
elif q == "Is my data safe here?":
    st.sidebar.info("""
Yes, your data is handled securely.

• Authentication is used (login system)
• Data is not shared publicly
• Only used for fraud detection

In real systems, additional security like encryption is used.
""")

#else:
#    st.sidebar.info("Please select a valid question.")
