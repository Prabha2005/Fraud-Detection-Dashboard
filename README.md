# Real-Time UPI Fraud Detection System

## Overview

The Real-Time UPI Fraud Detection System is an end-to-end machine-learning application that identifies potentially fraudulent UPI transactions.

The project combines an XGBoost classification model, FastAPI REST APIs and an interactive Streamlit dashboard. It supports real-time transaction checks, CSV batch prediction, Google Pay PDF analysis and live transaction simulation.

> This project is an educational prototype and is not intended for production banking use.

**Supported deployment:** local Docker Compose. AWS deployment is postponed and its templates are experimental; no GCP deployment is implemented.

---

## Live Demo

[Open the Fraud Detection Dashboard](https://fraud-detection-dashboard-a2ewk5y6yoo6mlw5z995dw.streamlit.app/)

This external demo's public availability is not verified; an unauthenticated check redirected to Streamlit authentication. Use the Docker Compose instructions below for the supported local deployment.

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
- Configurable SQLite database path using `DATABASE_PATH`
- Configurable audit-log storage using `AUDIT_LOG_PATH`

### Frontend and Visualization

- Streamlit
- Matplotlib

### PDF Processing

- pdfplumber
- Regular expressions

### Testing

- pytest
- FastAPI TestClient

### Containerization

- Docker
- Docker Compose

### CI/CD and Version Control

- GitHub Actions
- Git
- GitHub

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

The repository contains a synthetic UPI transaction dataset with 993 records:

- 947 legitimate transactions
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
- `COOKIE_PASSWORD`: A secure random value used to encrypt the frontend authentication cookie.

### Dataset Split

The dataset uses stratified splitting to preserve the fraud ratio:

| Split | Records | Purpose |
|---|---:|---|
| Training | 595 | Train the XGBoost model |
| Validation | 199 | Select the fraud threshold |
| Testing | 199 | Final unseen evaluation |

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
0.9615
```

A transaction is classified as fraud when:

```text
fraud probability >= saved decision threshold
```

---

## Current Evaluation Results

The model was evaluated on a 199-record synthetic holdout set.

| Metric | Result |
|---|---:|
| Accuracy | 0.9950 |
| Precision | 1.0000 |
| Recall | 0.8889 |
| F1 Score | 0.9412 |
| ROC-AUC | 1.0000 |
| PR-AUC | 1.0000 |

### Confusion Matrix

```text
[[190, 0],
 [  1, 8]]
```

This represents:

- 190 correctly classified legitimate transactions
- 8 correctly detected fraudulent transactions
- 0 false positives
- 1 false negative

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
| GET | `/` | No | Basic API response |
| GET | `/health` | No | Liveness health check |
| POST | `/signup` | No | Create a user account |
| POST | `/login` | No | Authenticate and obtain a JWT |
| POST | `/predict` | Bearer token | Upload a CSV for batch prediction |
| POST | `/predict_live` | Bearer token | Analyze a real-time transaction |
| POST | `/predict_pdf` | Bearer token | Analyze transactions extracted from a PDF |

### Health Check

```http
GET /health
```

Example response:

```json
{
  "status": "healthy",
  "service": "upi-fraud-detection-api"
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
  "decision_threshold": 0.961475,
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

If unnecessary globally installed pytest plugins cause high memory usage, automatic plugin loading can be disabled temporarily.

PowerShell:

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1"
python -m pytest tests -v
Remove-Item Env:PYTEST_DISABLE_PLUGIN_AUTOLOAD
```

## Continuous Integration

The GitHub Actions CI workflow installs the Python dependencies, runs Flake8 linting, and executes the automated pytest test suite.

After the test-and-lint job succeeds, Docker image builds run to validate the backend and frontend Dockerfiles:

- Backend Docker image build
- Frontend Docker image build

Docker image builds run only after the test-and-lint job succeeds.

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

### Configure the environment

```powershell
Copy-Item .env.example .env
```

Replace the placeholder values for `JWT_SECRET_KEY` and `COOKIE_PASSWORD` with locally generated secrets. Keep `.env` private; it is ignored by Git.

### Install dependencies

From the repository root, install both service requirement sets:

```powershell
python -m pip install -r backend/requirements.txt
python -m pip install -r frontend/requirements.txt
```

### Start the backend

In PowerShell, from the repository root:

```powershell
Set-Location backend
python -m uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

The backend is available at `http://127.0.0.1:8000`; health is at `/health` and Swagger UI is at `/docs`.

### Start the frontend

In a second terminal, from the repository root, set `FRAUD_API_URL` to `http://127.0.0.1:8000` in `.env`, then run:

```powershell
python -m streamlit run frontend/ui.py
```

Open `http://127.0.0.1:8501`.

---

## Docker Compose Deployment

Docker Compose is the supported deployment path. Copy `.env.example` to `.env` and replace both secret placeholders before starting the services. Compose supplies the frontend with the internal API URL `http://backend:8000`; do not use `localhost` between containers.

```powershell
docker compose up --build
```

- Dashboard: `http://127.0.0.1:8501`
- Backend API: `http://127.0.0.1:8000`
- Backend health: `http://127.0.0.1:8000/health`
- Backend API docs: `http://127.0.0.1:8000/docs`
- Frontend health: `http://127.0.0.1:8501/_stcore/health`

The host ports bind to loopback. `backend_data` and `backend_logs` are named local Docker volumes. `docker compose down` stops and removes the containers but preserves those volumes; do not use `-v` unless you intend to delete their data.

GitHub Actions CI is configured for tests and image-build checks. AWS is postponed; its workflow and templates are local-only, Git-ignored, and not included in a public checkout. GCP deployment is not implemented. See [DEPLOYMENT.md](DEPLOYMENT.md) for status and limitations.

---

## Validate without the PowerShell secret

Remove the shell variable so the application must load `.env`:

```powershell
Remove-Item Env:JWT_SECRET_KEY
```

---

## Current Limitations

- The dataset is synthetic and contains only 993 records.
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
- Docker containerization and multi-service orchestration
- CI/CD pipeline configuration using GitHub Actions
- Automated Docker image build validation
- Environment-based application configuration