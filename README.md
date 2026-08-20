# Real-Time UPI Fraud Detection System

## Overview

The Real-Time UPI Fraud Detection System is an end-to-end machine-learning application that identifies potentially fraudulent UPI transactions.

The project combines an XGBoost classification model, FastAPI REST APIs and an interactive Streamlit dashboard. It supports real-time transaction checks, CSV batch prediction, Google Pay PDF analysis and live transaction simulation.

> This project is an educational prototype and is not intended for production banking use.

---

## Live Demo

[Open the Fraud Detection Dashboard](https://fraud-detection-dashboard-a2ewk5y6yoo6mlw5z995dw.streamlit.app/)

---

## Features

- Real-time UPI fraud detection
- XGBoost-based prediction engine
- FastAPI REST API integration
- Interactive Streamlit dashboard
- CSV batch prediction
- Google Pay PDF analysis
- Live transaction simulation
- JWT-based authentication
- Fraud probability and risk scoring
- User transaction-history analysis
- Tuned fraud-decision threshold
- Prediction reasons
- Audit logging
- Automated preprocessing and API tests

---

## Technology Stack

### Machine Learning and Data Processing

- Python
- XGBoost
- Scikit-learn
- Pandas
- NumPy
- SHAP
- Joblib

### Backend

- FastAPI
- Uvicorn
- JWT authentication
- bcrypt password hashing
- SQLite

### Frontend and Visualization

- Streamlit
- Matplotlib

### PDF Processing

- pdfplumber
- Regular expressions

### Testing

- pytest
- FastAPI TestClient

---

## Project Architecture

```text
User
  |
  v
Streamlit Dashboard
  |
  v
FastAPI REST API
  |
  +--> JWT Authentication
  |
  v
Data Validation and Preprocessing
  |
  v
Nine-Feature Input Pipeline
  |
  v
XGBoost Model + Saved Decision Threshold
  |
  v
Prediction, Probability, Risk Level and Reasons
  |
  +--> Dashboard
  +--> SQLite Transaction History
  +--> Audit Log
```

---

## Dataset

The repository contains a synthetic UPI transaction dataset with 1,000 records:

- 954 legitimate transactions
- 46 fraudulent transactions

The target column is:

- `fraud_label`: `0` for legitimate and `1` for fraud

The dataset contains five basic transaction features. The application supports four additional behavioural features, but the training CSV does not contain the user-history and timestamp information required to calculate them.

Therefore, behavioural features use default values during training.

---

## Model Features

### Basic Transaction Features

| Feature | Description |
|---|---|
| `transaction_amount` | Monetary value of the transaction |
| `device_change` | Whether the transaction uses a changed device |
| `merchant_risk` | Risk score associated with the merchant |
| `geo_velocity` | Geographic movement indicator |
| `hour_of_day` | Hour when the transaction occurred |

### Behavioural Features

| Feature | Description |
|---|---|
| `txn_count_24h` | Number of user transactions in the previous 24 hours |
| `amount_zscore` | Difference between the current amount and normal user behaviour |
| `amount_vs_max` | Current amount compared with the user's historical maximum |
| `amount_sum_24h` | Total amount transacted by the user in 24 hours |

The preprocessing pipeline always returns the same nine features in the correct order.

During real-time prediction, behavioural values are calculated from the authenticated user's transaction history. In the current synthetic training dataset, these features are constant defaults and therefore have zero learned model importance.

---

## Data Preprocessing

The preprocessing pipeline performs:

- Required-column validation
- Nine-feature ordering
- Numeric type conversion
- Invalid-value rejection
- Feature-range validation
- Default behavioural-feature creation
- Geographic-velocity absolute-value conversion
- Geographic-velocity clipping at 500

Examples of rejected data include:

- Non-numeric transaction amounts
- Transaction amounts less than or equal to zero
- Invalid device-change values
- Merchant-risk values outside `0–1`
- Transaction hours outside `0–23`
- Negative behavioural counts or totals

The project does not currently perform feature scaling or categorical encoding because all model inputs are numeric and XGBoost does not require normalized inputs.

---

## Class-Imbalance Handling

The dataset contains significantly fewer fraud records than legitimate records.

Class imbalance is handled using XGBoost's `scale_pos_weight` parameter. SMOTE is not used in the current implementation.

The class weight is calculated only from the training split:

```text
Training legitimate records: 567
Training fraud records: 28
scale_pos_weight: 20.2500
```

The calculation is:

```text
scale_pos_weight = legitimate training records / fraud training records
```

The value is:

```text
567 ÷ 28 = 20.25
```

---

## Model Training

### Algorithm

The project uses `XGBClassifier`.

Main configuration:

- Estimators: 150
- Maximum depth: 5
- Learning rate: 0.1
- Subsample: 0.8
- Column sample by tree: 0.8
- Evaluation metric: log loss
- Random state: 42
- Class imbalance: `scale_pos_weight`

### Dataset Split

The dataset uses stratified splitting to preserve the fraud ratio:

| Split | Records | Purpose |
|---|---:|---|
| Training | 600 | Train the XGBoost model |
| Validation | 200 | Select the fraud threshold |
| Testing | 200 | Final unseen evaluation |

---

## Decision-Threshold Selection

The model generates a fraud probability for each transaction.

Instead of using a hard-coded threshold of `0.5`, the training pipeline:

1. Generates probabilities for the validation set.
2. Calculates precision and recall at different thresholds.
3. Calculates the F1 score for each threshold.
4. Selects the threshold with the best validation F1 score.
5. Saves the threshold as a model artifact.
6. Loads the saved threshold during prediction.

The current selected threshold is approximately:

```text
0.8123
```

A transaction is classified as fraud when:

```text
fraud probability >= saved decision threshold
```

---

## Current Evaluation Results

The model was evaluated on a 200-record synthetic holdout set.

| Metric | Result |
|---|---:|
| Accuracy | 1.0000 |
| Precision | 1.0000 |
| Recall | 1.0000 |
| F1 Score | 1.0000 |
| ROC-AUC | 1.0000 |
| PR-AUC | 1.0000 |

### Confusion Matrix

```text
[[191, 0],
 [  0, 9]]
```

This represents:

- 191 correctly classified legitimate transactions
- 9 correctly classified fraudulent transactions
- 0 false positives
- 0 false negatives

> Important: These results apply only to the current synthetic holdout set, which contains nine fraud examples. The dataset is small and strongly separable, with `merchant_risk` dominating model importance. These results do not prove real-world performance. A larger external dataset is required to evaluate generalization.

The complete generated evaluation report is stored in:

```text
backend/model/evaluation_metrics.json
```

---

## Model Explainability

The project supports:

- XGBoost feature importance
- Basic prediction reasons
- SHAP-based feature contributions
- Human-readable feature labels

In the current trained model, the five basic transaction features influence prediction. The four behavioural features have zero importance because they are constant in the training dataset.

---

## API Endpoints

| Method | Endpoint | Authentication | Purpose |
|---|---|---|---|
| GET | `/` | No | Check whether the API is running |
| POST | `/signup` | No | Create a user account |
| POST | `/login` | No | Authenticate and obtain a JWT |
| POST | `/predict` | Bearer token | Upload a CSV for batch prediction |
| POST | `/predict_live` | Bearer token | Analyze a real-time transaction |
| POST | `/predict_pdf` | Bearer token | Analyze transactions extracted from a PDF |
| POST | `/retrain` | No | Experimental model-retraining endpoint |

### Health Check

```http
GET /
```

Example response:

```json
{
  "status": "UPI Fraud Detection API is running"
}
```

### CSV Prediction

```http
POST /predict
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

The endpoint accepts a CSV file containing:

```text
transaction_amount
device_change
merchant_risk
geo_velocity
hour_of_day
```

Example prediction object:

```json
{
  "prediction": "Fraud",
  "probability": 0.964,
  "risk_level": "High Risk",
  "decision_threshold": 0.812316,
  "reasons": [
    "transaction_amount contributed",
    "geo_velocity contributed"
  ],
  "latency_ms": 14.17
}
```

---

## Dashboard

The Streamlit dashboard provides four main workflows.

### CSV Upload

- Upload multiple transactions
- View fraud and legitimate counts
- Review risk levels
- Inspect suspicious transactions
- Download prediction results

### Real-Time Check

- Enter a single transaction
- Receive an immediate prediction
- View fraud probability and risk level
- Review behavioural warnings
- View available prediction reasons

### Live Simulation

- Generate ten simulated transactions
- Send each transaction to the API
- Display a live fraud-risk graph
- Track total fraud detections
- Download simulation results

### Google Pay PDF Analysis

- Upload a Google Pay PDF
- Extract transaction amounts
- Generate fraud predictions
- Download the analyzed results

---

## Automated Tests

The project includes tests for:

- Nine-feature preprocessing
- Behavioural-feature preservation
- Invalid transaction-amount rejection
- Authentication enforcement
- Authenticated CSV prediction responses

Run all tests:

```bash
python -m pytest tests -v
```

Expected result:

```text
5 passed
```

If unnecessary globally installed pytest plugins cause high memory usage, automatic plugin loading can be disabled temporarily.

PowerShell:

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1"
python -m pytest tests -v
Remove-Item Env:PYTEST_DISABLE_PLUGIN_AUTOLOAD
```

---

## Project Structure

```text
Fraud-Detection-Dashboard/
├── backend/
│   ├── app.py
│   ├── auth.py
│   ├── audit_logger.py
│   ├── database.py
│   ├── models.py
│   ├── pdf_parser.py
│   ├── predict.py
│   ├── preprocess.py
│   ├── retrain.py
│   ├── shap_utils.py
│   ├── train_model.py
│   ├── velocity_features.py
│   └── model/
│       ├── xgboost_model.pkl
│       ├── fraud_threshold.pkl
│       ├── shap_explainer.pkl
│       ├── evaluation_metrics.json
│       └── training_stats.json
├── frontend/
│   └── ui.py
├── sample_data/
│   ├── upi_fraud_demo.csv
│   └── upi_fraud_predict.csv
├── tests/
│   ├── test_preprocess.py
│   └── test_predict_api.py
└── README.md
```

---

## Running the Project Locally

### Install Backend Dependencies

```bash
pip install -r backend/requirements.txt
```

### Start FastAPI

```bash
cd backend
uvicorn app:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

### Start Streamlit

From the project root:

```bash
streamlit run frontend/ui.py
```

---

## Current Limitations

- The dataset is synthetic and contains only 1,000 records.
- The test set contains only nine fraud cases.
- Behavioural features are constant during training and have zero model importance.
- Some PDF features are simulated because they are unavailable in the statement.
- PDF transactions below ₹50 are currently overridden as legitimate.
- The retraining workflow requires reviewed fraud labels that are not currently stored.
- Real-world banking data and external validation are not included.
- The application is an educational prototype, not a production banking system.

---

## Future Improvements

- Train and validate using a larger real-world dataset
- Add user and timestamp fields to training data
- Train the model using meaningful behavioural features
- Add model and data-drift monitoring
- Improve PDF feature extraction
- Remove fixed PDF prediction overrides
- Add reviewed fraud-label collection
- Add Kafka-based transaction streaming
- Move from SQLite to PostgreSQL
- Improve secret and authentication management
- Expand automated API and integration tests

---

## Learning Outcomes

Through this project, I gained hands-on experience in:

- End-to-end machine-learning application development
- Fraud-detection concepts
- Data validation and preprocessing
- Feature engineering
- Class-imbalance handling
- XGBoost model training
- Validation-based threshold tuning
- Model evaluation
- FastAPI development
- JWT authentication
- REST API integration
- Streamlit dashboard development
- Automated testing
- Model deployment