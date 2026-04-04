import os
import pandas as pd
import joblib
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score

from backend.preprocess import preprocess   # 🔥 IMPORTANT


# ----------------------------
# Feature Order
# ----------------------------
FEATURE_ORDER = [
    "transaction_amount",
    "device_change",
    "merchant_risk",
    "geo_velocity",
    "hour_of_day"
]


# ----------------------------
# Load Dataset
# ----------------------------
df = pd.read_csv("sample_data/upi_fraud_demo.csv")

missing_cols = [col for col in FEATURE_ORDER + ["fraud_label"] if col not in df.columns]
if missing_cols:
    raise ValueError(f"Missing required columns: {missing_cols}")


# ----------------------------
# Apply SAME preprocessing
# ----------------------------
X = preprocess(df)   # 🔥 FIX
y = df["fraud_label"]


# ----------------------------
# Train-Test Split
# ----------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.2,
    stratify=y,
    random_state=42
)


# ----------------------------
# Train Model
# ----------------------------
model = XGBClassifier(
    n_estimators=150,
    max_depth=5,
    learning_rate=0.1,
    subsample=0.8,
    colsample_bytree=0.8,
    eval_metric="logloss",
    random_state=42
)

model.fit(X_train, y_train)


# ----------------------------
# Evaluation
# ----------------------------
y_pred = model.predict(X_test)
y_prob = model.predict_proba(X_test)[:, 1]

print("\n📊 Model Performance:")
print(f"Accuracy  : {accuracy_score(y_test, y_pred):.4f}")
print(f"Precision : {precision_score(y_test, y_pred):.4f}")
print(f"Recall    : {recall_score(y_test, y_pred):.4f}")
print(f"F1 Score  : {f1_score(y_test, y_pred):.4f}")
print(f"ROC-AUC   : {roc_auc_score(y_test, y_prob):.4f}")


# ----------------------------
# Feature Importance (DEBUG)
# ----------------------------
importance = model.feature_importances_
for i, col in enumerate(FEATURE_ORDER):
    print(f"{col}: {importance[i]:.4f}")


# ----------------------------
# Save Model
# ----------------------------
os.makedirs("model", exist_ok=True)
joblib.dump(model, "model/xgboost_model.pkl")

print("\n✅ Model saved successfully")