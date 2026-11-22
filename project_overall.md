# UPI Fraud Detection Dashboard - Complete Project Overview

> Deployment status: Docker Compose is supported. AWS is postponed; its workflow and templates are experimental and unvalidated. GCP deployment is not implemented.

## 1. Project Summary

This repository implements an end-to-end educational UPI fraud-detection system. It combines:

- A FastAPI REST API
- An XGBoost binary classification model
- SHAP-based prediction explanations
- A Streamlit dashboard
- SQLite user and transaction storage
- JWT authentication and bcrypt password hashing
- CSV, real-time, transaction-simulation, and Google Pay PDF workflows
- JSON-lines audit logging
- Docker and Docker Compose deployment
- GitHub Actions CI; postponed AWS templates/workflow are local-only and Git-ignored

The intended answer is either `Legit` or `Fraud`, accompanied by:

- Fraud probability
- Risk level
- Tuned fraud-decision threshold
- Human-readable feature reasons
- Optional SHAP contributions
- Inference latency for CSV predictions
- Optional behavior and request-context information

This is a prototype for learning and demonstration. It is not a substitute for a bank-grade fraud platform or real-world anti-fraud system.

---

## 2. High-Level Architecture

```text
Streamlit user interface
        |
        | HTTPS/HTTP REST calls
        v
FastAPI application
        |
        +--> JWT verification
        +--> Pydantic input validation
        +--> CSV/PDF parsing
        +--> Preprocessing
        +--> SQLite behavioral history
        +--> XGBoost probability prediction
        +--> Tuned decision threshold
        +--> SHAP / feature explanations
        +--> JSONL audit logger
        |
        v
Streamlit results, charts, tables, and downloads
```

Model artifacts and training data are stored locally in the repository. Runtime state is stored in SQLite and JSONL files.

---

## 3. Repository Structure

```text
Fraud-Detection-Dashboard/
├── backend/
│   ├── app.py                 FastAPI routes and application startup
│   ├── auth.py                JWT creation/verification and password hashing
│   ├── audit_logger.py        Prediction audit-log writer
│   ├── database.py            SQLite connection and table creation
│   ├── models.py              Pydantic request schemas
│   ├── pdf_parser.py          Standalone Google Pay PDF parser
│   ├── predict.py             Model loading, preprocessing, risk, and explanations
│   ├── preprocess.py          Feature normalization and validation
│   ├── retrain.py             Transaction-based retraining attempt
│   ├── shap_utils.py          Human-readable SHAP explanations
│   ├── train_model.py         Model training, threshold tuning, and artifact generation
│   ├── velocity_features.py   Past-transaction behavioral feature calculation
│   ├── users.db               Runtime SQLite database (Git-ignored; not published)
│   ├── requirements.txt       Backend dependencies
│   └── model/
│       ├── xgboost_model.pkl
│       ├── fraud_threshold.pkl
│       ├── shap_explainer.pkl
│       ├── evaluation_metrics.json
│       └── training_stats.json
├── frontend/
│   ├── ui.py                  Streamlit dashboard
│   ├── requirements.txt       Frontend dependencies
│   ├── Dockerfile
│   └── images/
├── sample_data/
│   ├── upi_fraud_demo.csv     Training dataset
│   └── upi_fraud_predict.csv  Five-feature prediction CSV
├── tests/
│   ├── test_preprocess.py
│   └── test_predict_api.py
├── aws/                       Local-only templates (Git-ignored; not published)
│   ├── apprunner-backend.json
│   ├── apprunner-frontend.json
│   ├── ecs-task-backend.json
│   └── ecs-task-frontend.json
├── .github/workflows/
│   ├── ci.yml
│   └── cd-aws.yml             Local-only workflow (Git-ignored; not published)
├── .devcontainer/devcontainer.json
├── docker-compose.yml
├── DEPLOYMENT.md
├── .env.example
├── .gitignore
└── README.md

`project_overall.md` is this repository-wide technical description.

---

## 4. Runtime Technologies

### Machine learning and data

- Python 3.11
- Pandas
- NumPy
- XGBoost
- Scikit-learn
- SHAP
- Joblib
- SciPy

### Backend and authentication

- FastAPI
- Uvicorn
- Pydantic
- PyJWT
- bcrypt
- Python multipart upload support
- SQLite
- python-dotenv

### Frontend and visualization

- Streamlit
- Requests
- Matplotlib
- Plotly
- Pillow
- `streamlit-cookies-manager`

### Other tools

- pdfplumber
- pytest
- httpx
- Flake8
- Docker and Docker Compose
- GitHub Actions
- AWS deployment templates and workflow (local-only, Git-ignored, postponed)

---

## 5. Backend Application

### 5.1 Startup behavior

[backend/app.py](backend/app.py) performs the following at startup:

1. Loads or sets up the FastAPI application.
2. Loads the optional SHAP explainer from `backend/model/shap_explainer.pkl`.
3. Creates the `users` and `transactions` tables.
4. Reads comma-separated CORS origins from `ALLOWED_ORIGINS`.
5. Uses local Streamlit origins as defaults:
   - `http://localhost:8501`
   - `http://127.0.0.1:8501`
6. Configures methods and headers allowed through CORS.
7. Defines a cached model loader for the XGBoost artifact.

The backend listens on port `8000` by default. `PORT` controls container startup and direct Uvicorn startup.

### 5.2 Health endpoints

| Method | Route | Purpose |
|---|---|---|
| `GET` | `/` | General service-running response |
| `GET` | `/health` | Liveness and container health response |

Example root response:

```json
{"status": "UPI Fraud Detection API is running"}
```

Example health response:

```json
{"status": "healthy", "service": "upi-fraud-detection-api"}
```

### 5.3 Authentication endpoints

| Method | Route | Authentication | Purpose |
|---|---|---|---|
| `POST` | `/signup` | None | Create a local account |
| `POST` | `/login` | None | Return a JWT |

Signup:

```sql
INSERT INTO users (username, password) VALUES (?, ?)
```

The password is converted with bcrypt before storage.

Login:

```sql
SELECT * FROM users WHERE username = ?
```

The stored bcrypt hash is checked against the supplied password. On success, the backend creates a signed JWT containing:

- `user`: authenticated username
- `iat`: issue time
- `exp`: expiration time

JWT configuration:

- Algorithm: `HS256`
- Default expiration: 60 minutes
- Secret key environment variable: `JWT_SECRET_KEY`
- Secret length: at least 32 characters

Protected endpoints use HTTP Bearer authentication. Expired and invalid JWTs receive `401 Unauthorized` responses.

### 5.4 Prediction endpoints

| Method | Route | Authentication | Input | Output |
|---|---|---|---|---|
| `POST` | `/predict` | Bearer JWT | CSV upload | Batch prediction rows |
| `POST` | `/predict_live` | Bearer JWT | JSON transaction | One prediction plus context |
| `POST` | `/predict_pdf` | Bearer JWT | PDF upload | Extracted and classified transactions |

#### CSV prediction

The `/predict` endpoint:

1. Rejects filenames that do not end in `.csv`.
2. Reads the CSV with Pandas.
3. Removes `fraud_label` if it is present.
4. Adds four missing behavioral columns with default values.
5. Verifies all required columns exist.
6. Enforces feature order.
7. Runs preprocessing and XGBoost inference.
8. Returns prediction, probability, risk level, threshold, reasons, and latency.

CSV inputs are expected to contain:

- `transaction_amount`
- `device_change`
- `merchant_risk`
- `geo_velocity`
- `hour_of_day`

Default behavioral values for CSV uploads:

- `txn_count_24h = 0`
- `amount_zscore = 0`
- `amount_vs_max = 1`
- `amount_sum_24h = 0`

Example response row:

```json
{
  "prediction": "Fraud",
  "probability": 0.964,
  "risk_level": "High Risk",
  "decision_threshold": 0.961475,
  "reasons": ["transaction_amount contributed", "geo_velocity contributed"],
  "latency_ms": 14.17
}
```

#### Real-time prediction

The `/predict_live` endpoint accepts `Transaction` objects from [backend/models.py](backend/models.py):

| Field | Validation |
|---|---|
| `amount` | Greater than zero |
| `time` | Integer between 0 and 23 |
| `location` | Optional string; contextual only |
| `device_change` | Integer 0 or 1, default `0` |
| `merchant_risk` | Float 0 through 1, default `0.0` |
| `geo_velocity` | Non-negative float, default `0.0` |

The backend:

1. Maps `amount` to `transaction_amount`.
2. Maps `time` to `hour_of_day`.
3. Removes `location` from model input.
4. Calculates authenticated-user behavior features.
5. Preprocesses and predicts.
6. Retrieves recent stored amounts.
7. Adds a behavior warning when the current amount is more than three times the recent average.
8. Stores the transaction in SQLite.
9. Writes the prediction to the audit log.
10. Returns prediction context and optional explanations.

The behavior flag is:

```text
Unusual high transaction compared to history
```

It is a heuristic, not a separate machine-learning model.

The response includes:

- Prediction
- Fraud probability
- Risk level
- Decision threshold
- Prediction reasons
- Behavior flag
- Request IP address
- User-Agent/device string
- SHAP or fallback explanation

#### PDF prediction

The `/predict_pdf` endpoint:

1. Requires a `.pdf` filename.
2. Saves the upload to a temporary PDF file.
3. Extracts text with pdfplumber.
4. Searches for:
   - `Paid to` or `Received from`
   - Indian rupee amounts such as `₹100` or `₹1,000`
5. Tracks the current merchant name.
6. Treats a merchant as new on first occurrence.
7. Adds random or placeholder values for unavailable fields:
   - `merchant_risk`
   - `geo_velocity`
   - `hour_of_day`
   - `device_change = 0`
8. Adds default behavioral features.
9. Runs standard model prediction.
10. Forces transactions below ₹50 to `Legit` with probability `0.001`.
11. Generates explanations and audit records.

The standalone [backend/pdf_parser.py](backend/pdf_parser.py) has a simpler parser that returns a five-column DataFrame using:

- `device_change = 0`
- `merchant_risk = 0.5`
- `geo_velocity = 0`
- `hour_of_day = 12`

It is available as a helper but the main FastAPI PDF route implements additional extraction and response logic itself.

---

## 6. Database Schema

The SQLite database defaults to a runtime file at `backend/users.db`; the file is ignored by Git and is not included in the repository. `DATABASE_PATH` can override it. Docker Compose overrides the path to its named `backend_data` volume.

`get_db()` creates the database directory, opens SQLite, and enables `sqlite3.Row` so columns can be accessed by name.

### 6.1 Users table

```sql
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
);
```

| Column | Type | Constraint |
|---|---|---|
| `id` | INTEGER | Primary key, autoincrement |
| `username` | TEXT | Unique |
| `password` | TEXT | bcrypt password hash |

### 6.2 Transactions table

```sql
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    amount REAL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    ip TEXT,
    device TEXT
);
```

| Column | Type | Constraint/default |
|---|---|---|
| `id` | INTEGER | Primary key, autoincrement |
| `username` | TEXT | No foreign key |
| `amount` | REAL | None |
| `timestamp` | DATETIME | `CURRENT_TIMESTAMP` |
| `ip` | TEXT | Request IP |
| `device` | TEXT | User-Agent value |

### 6.3 Relationship

The tables share `username` logically:

```text
users.username 1 ----< transactions.username
```

The relationship is **not enforced by SQLite**:

- No foreign key exists.
- `username` is not an explicit user ID foreign key.
- Unknown usernames could be inserted into transactions.
- The implementation should not rely on database referential integrity in its current form.

There is no `fraud_label` column in the existing schema, even though retraining code checks for it.

---

## 7. SQL Operations Currently Implemented

The project currently uses direct SQLite queries and parameterized values.

### Table creation

```sql
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
);

CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    amount REAL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    ip TEXT,
    device TEXT
);
```

### User operations

```sql
INSERT INTO users (username, password) VALUES (?, ?);
SELECT * FROM users WHERE username = ?;
```

### Transaction operations

```sql
INSERT INTO transactions (username, amount, ip, device)
VALUES (?, ?, ?, ?);

SELECT amount
FROM transactions
WHERE username = ?
ORDER BY id DESC
LIMIT 5;

SELECT amount, timestamp
FROM transactions
WHERE username = ?
ORDER BY id DESC;

SELECT * FROM transactions;
```

### SQL feature assessment

The current SQL does **not** use:

- `JOIN`
- `GROUP BY`
- `HAVING`
- SQL aggregate functions (`COUNT`, `SUM`, `AVG`, `MIN`, `MAX`)
- Subqueries

Aggregation is performed in Python:

- Recent average:

  ```python
  avg_amount = sum(row["amount"] for row in history) / len(history)
  ```

- User mean and standard deviation:

  ```python
  np.mean(all_amounts)
  np.std(all_amounts)
  ```

- User maximum:

  ```python
  max(all_amounts)
  ```

- 24-hour transaction count and sum:

  ```python
  len(amounts_24h)
  sum(amounts_24h)
  ```

---

## 8. Nine-Feature Model Contract

The model always consumes exactly nine features in this order:

| Position | Feature | Meaning |
|---:|---|---|
| 1 | `transaction_amount` | Transaction value |
| 2 | `device_change` | 1 if a device changed, otherwise 0 |
| 3 | `merchant_risk` | Merchant risk in `[0, 1]` |
| 4 | `geo_velocity` | Geographic velocity indicator |
| 5 | `hour_of_day` | Transaction hour from 0 to 23 |
| 6 | `txn_count_24h` | Transactions found for the user in 24 hours |
| 7 | `amount_zscore` | Transaction amount deviation from user mean |
| 8 | `amount_vs_max` | Transaction amount divided by user's historical maximum |
| 9 | `amount_sum_24h` | Total amount in the user's 24-hour window |

### Basic features

The CSV and real-time workflows supply:

- `transaction_amount`
- `device_change`
- `merchant_risk`
- `geo_velocity`
- `hour_of_day`

### Behavioral features

For live transactions, [backend/velocity_features.py](backend/velocity_features.py) calculates:

- Recent transactions in the past 24 hours
- Sum of those amounts
- Z-score against all stored user amounts
- Ratio of the current amount to the user's maximum amount

The timestamp calculation uses `datetime.fromisoformat()`. Invalid timestamps are ignored without stopping prediction.

CSV and PDF workflows use default behavioral values because they do not have a reliable authenticated transaction history in the current data.

---

## 9. Preprocessing and Validation

[backend/preprocess.py](backend/preprocess.py) provides the shared preprocessing pipeline.

It:

1. Rejects an empty DataFrame.
2. Requires all five basic columns.
3. Adds missing behavioral features with defaults.
4. Converts all nine columns to numeric values.
5. Rejects missing or non-numeric values and reports row indices.
6. Requires `transaction_amount > 0`.
7. Requires `device_change` to be 0 or 1.
8. Requires `merchant_risk` to be from 0 through 1.
9. Requires `hour_of_day` to be from 0 through 23.
10. Rejects negative `txn_count_24h`.
11. Rejects negative `amount_vs_max`.
12. Rejects negative `amount_sum_24h`.
13. Converts negative `geo_velocity` values to absolute values.
14. Clips `geo_velocity` to a maximum of 500.
15. Returns exactly the nine-model-feature columns in model order.

It does not perform:

- Standardization
- Normalization
- One-hot encoding
- Scaling

All model inputs are numeric, and XGBoost accepts the raw feature values after range cleaning.

---

## 10. Model Training

[backend/train_model.py](backend/train_model.py) trains the model from [sample_data/upi_fraud_demo.csv](sample_data/upi_fraud_demo.csv).

Training data has six columns:

```text
transaction_amount
device_change
merchant_risk
geo_velocity
hour_of_day
fraud_label
```

The behavioral features are not present in the training CSV, so preprocessing gives them these defaults:

- `txn_count_24h = 0`
- `amount_zscore = 0`
- `amount_vs_max = 1`
- `amount_sum_24h = 0`

### 10.1 Dataset distribution

- Total records: 993
- Legitimate records: 947
- Fraud records: 46

The target is binary:

- `0`: Legitimate
- `1`: Fraud

### 10.2 Split

The data is split with stratification and `random_state=42`:

- 60% training: 595 records
- 20% validation: 199 records
- 20% test: 199 records

The validation set is used only to choose a decision threshold. The test set is used only for final evaluation.

### 10.3 XGBoost configuration

```text
n_estimators = 150
max_depth = 5
learning_rate = 0.1
subsample = 0.8
colsample_bytree = 0.8
eval_metric = logloss
random_state = 42
scale_pos_weight = 20.25
```

The class weight is:

```text
training legitimate records / training fraud records
567 / 28 = 20.25
```

SMOTE and other resampling tools are not used in the training script.

### 10.4 Threshold tuning

The script calculates precision-recall curves on validation probabilities, calculates F1 for threshold candidates, and chooses the threshold with maximum validation F1.

The selected threshold is approximately:

```text
0.9614746570587158
```

During prediction:

```text
fraud_probability >= saved_threshold => Fraud
fraud_probability < saved_threshold  => Legit
```

The threshold is separate from the probability-to-risk labels:

- `>= 0.8`: High Risk
- `>= 0.4`: Medium Risk
- `< 0.4`: Low Risk

A transaction can therefore have a high/medium/low risk label that differs from the binary fraud decision.

---

## 11. Evaluation Results

Artifacts show the following holdout test result:

| Metric | Result |
|---|---:|
| Dataset records | 993 |
| Training records | 595 |
| Validation records | 199 |
| Test records | 199 |
| Accuracy | 0.9949748744 |
| Precision | 1.0 |
| Recall | 0.8888888889 |
| F1 | 0.9411764706 |
| ROC-AUC | 1.0 |
| PR-AUC | 1.0000000002 |

Confusion matrix:

```text
[[190,   0],
 [  1,   8]]
```

Interpretation:

- 190 true negatives
- 8 true positives
- 0 false positives
- 1 false negative

Classification-report support:

- Legitimate: 190 test records
- Fraud: 9 test records

Because only nine fraud records exist in the test set, these metrics are not evidence of production-grade real-world performance.

The complete metrics are in [backend/model/evaluation_metrics.json](backend/model/evaluation_metrics.json).

---

## 12. Model Artifacts

### XGBoost model

[backend/model/xgboost_model.pkl](backend/model/xgboost_model.pkl) contains the trained `XGBClassifier`.

### Decision threshold

[backend/model/fraud_threshold.pkl](backend/model/fraud_threshold.pkl) contains the tuned probability threshold.

### SHAP explainer

[backend/model/shap_explainer.pkl](backend/model/shap_explainer.pkl) contains a `TreeExplainer`.

### Training statistics

[backend/model/training_stats.json](backend/model/training_stats.json) contains per-feature training means and standard deviations.

### Evaluation metrics

[backend/model/evaluation_metrics.json](backend/model/evaluation_metrics.json) contains:

- Dataset and split sizes
- Class totals
- Scale weight
- Selected threshold
- Accuracy
- Precision
- Recall
- F1
- ROC-AUC
- PR-AUC
- Confusion matrix
- Classification report

---

## 13. Prediction Explanation

### Feature reasons

[backend/predict.py](backend/predict.py) calculates reasons only for fraud predictions. It uses:

```python
absolute(feature_importance * transaction_feature_value)
```

The two largest values are returned as strings such as:

```text
transaction_amount contributed
geo_velocity contributed
```

This is a heuristic explanation, not a complete SHAP calculation.

### SHAP explanations

[backend/shap_utils.py](backend/shap_utils.py) converts SHAP values to:

- Human-readable feature label
- Input feature value
- SHAP contribution
- Direction: increases or decreases fraud risk
- Top reasons
- SHAP base score

The SHAP labels include all nine features.

If the SHAP explainer is unavailable, the real-time route falls back to the basic `row["reasons"]` list.

---

## 14. Behavioral Feature Calculation

[backend/velocity_features.py](backend/velocity_features.py) queries past transaction amounts and timestamps for the authenticated user:

```sql
SELECT amount, timestamp
FROM transactions
WHERE username = ?
ORDER BY id DESC;
```

Features are calculated as follows:

| Feature | Calculation |
|---|---|
| `txn_count_24h` | Number of rows whose timestamp is within 24 hours |
| `amount_sum_24h` | Sum of those 24-hour amounts |
| `amount_zscore` | `(current - mean_all) / std_all`, or 0 if standard deviation is zero |
| `amount_vs_max` | `current / max_all`, or 1 if no positive maximum exists |

If no transactions exist:

- `txn_count_24h = 0`
- `amount_zscore = 0`
- `amount_vs_max = 1`
- `amount_sum_24h = 0`

Timestamp parsing is local naive datetime parsing; timezone-aware or malformed values may not contribute to 24-hour totals.

---

## 15. Audit Logging

[backend/audit_logger.py](backend/audit_logger.py) writes one JSON object per line.

Default path:

```text
logs/audit_log.jsonl
```

`AUDIT_LOG_PATH` overrides the location.

Each entry receives a UTC timestamp and the supplied prediction fields. Example:

```json
{
  "timestamp": "2026-01-01T12:00:00.000000",
  "user": "example_user",
  "amount": 5000,
  "prediction": "Fraud",
  "probability": 0.982,
  "ip": "127.0.0.1"
}
```

The PDF route also adds `source: "pdf"`.

The audit log directory is created automatically.

---

## 16. Streamlit Frontend

[frontend/ui.py](frontend/ui.py) is the dashboard implementation.

### Startup and security

The frontend:

- Loads project `.env` variables.
- Requires `COOKIE_PASSWORD` at startup.
- Uses `EncryptedCookieManager`.
- Stores the JWT in Streamlit session state and an encrypted cookie.
- Stops all protected dashboard rendering unless a token exists.
- Provides login and signup forms.
- Provides a logout button that clears session and cookie state.
- Reads `FRAUD_API_URL` from the environment; the application has no hosted-URL fallback. `.env.example` sets the local URL and Compose sets `http://backend:8000`.
- Sets Streamlit's page title and wide layout.

### Sidebar navigation

The sidebar contains:

- Dashboard/About page selection
- Logout button
- AI assistant quick questions
- A chat input
- A question dropdown
- Educational fraud and UPI safety responses

The assistant is rule-based and keyword-based. It does not call an AI model or API.

### About page

The About page explains:

- The purpose of the dashboard
- UPI and digital-payment basics
- Supported features
- Real-time and bulk analysis
- The risks of digital transactions

### Dashboard tabs

#### Tab 1: Upload Transactions

- Accepts a CSV file.
- Sends it to `/predict` with a Bearer token.
- Displays total, fraud, and legitimate counts.
- Displays high-risk and medium-risk counts.
- Highlights fraud rows.
- Shows suspicious transactions sorted by probability.
- Displays:
  - Probability histogram
  - Legitimate/fraud bar chart
  - Prediction/explanation table
- Downloads results as `fraud_results.csv`.

High-risk and medium-risk summaries in this tab use frontend probability thresholds:

- High: probability `> 0.8`
- Medium: probability `> 0.5` and `<= 0.8`

#### Tab 2: Real-Time Check

The user enters:

- Transaction amount
- Device-changed value
- Merchant risk
- Geographic velocity
- Hour of day

The frontend sends:

```json
{
  "amount": 500,
  "time": 12,
  "location": "India",
  "device_change": 0,
  "merchant_risk": 0.2,
  "geo_velocity": 50
}
```

It displays:

- Prediction
- Probability
- Risk level
- IP address
- User-Agent
- Behavior warning
- Reasons
- SHAP top reasons
- Probability bar chart
- Downloadable real-time result

#### Tab 3: Live Simulation

The simulation:

1. Generates 10 transactions.
2. Randomizes amount, geo velocity, hour, device-change, and merchant-risk values.
3. Sends each to `/predict_live`.
4. Updates live status, trend, and summary placeholders.
5. Tracks fraud detections.
6. Adds a one-second delay between transactions.
7. Downloads all simulation response rows.

The simulation is a frontend demonstration and does not represent a real transaction stream.

#### Tab 4: Upload Google Pay PDF

- Accepts a PDF.
- Sends it to `/predict_pdf`.
- Displays returned JSON and a fraud summary.
- Downloads `pdf_results.csv`.

The PDF route currently extracts amounts and merchant names heuristically. It is not a guaranteed parser for every Google Pay statement format.

---

## 17. Retraining Workflow

[backend/retrain.py](backend/retrain.py) contains an optional retraining function that:

1. Opens the database.
2. Runs `SELECT * FROM transactions`.
3. Returns if no rows exist.
4. Maps `amount` to `transaction_amount`.
5. Sets `geo_velocity = 50`.
6. Sets `hour_of_day = 12`.
7. Creates placeholder behavioral columns if absent.
8. Returns unless `fraud_label` exists.
9. Preprocesses the data.
10. Uses the nine model features.
11. Trains a 150-tree XGBoost classifier.
12. Writes `backend/model/xgboost_model.pkl`.

Current limitations:

- The `transactions` table does not define `fraud_label`.
- Retraining cannot proceed unless an external migration or updated schema adds labels.
- It does not update `fraud_threshold.pkl` or `shap_explainer.pkl`.
- It does not evaluate or split the new data.
- It does not save an updated metrics or training-statistics report.
- It does not close the SQLite connection explicitly.
- The function should be treated as an incomplete prototype.

---

## 18. Test Coverage

### Preprocessing tests

[tests/test_preprocess.py](tests/test_preprocess.py) verifies:

- Nine output features are returned.
- Behavioral defaults are zero/one as designed.
- Supplied behavioral values are preserved.
- Invalid text transaction amounts raise `ValueError`.

### API tests

[tests/test_predict_api.py](tests/test_predict_api.py) verifies:

- `/` responds successfully.
- `/health` returns `healthy`.
- `/predict` rejects unauthenticated requests.
- An authenticated CSV request returns two prediction objects.
- Required response fields exist.
- Predictions are either `Fraud` or `Legit`.
- Probability and threshold remain in `[0, 1]`.
- Risk labels are recognized.
- Reasons are lists.
- Latency is non-negative.

### CI test environment

The CI workflow:

- Uses Python 3.11.
- Installs both backend and development dependencies.
- Runs Flake8 syntax checks.
- Runs `pytest tests/ -v --junitxml=test-results.xml`.
- Uploads JUnit test artifacts.
- Builds both Docker images.

### Running tests locally

```powershell
python -m pytest tests -v
```

If globally installed pytest plugins cause problems:

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD="1"
python -m pytest tests -v
Remove-Item Env:PYTEST_DISABLE_PLUGIN_AUTOLOAD
```

---

## 19. Environment Variables

### Backend

| Variable | Required | Default | Purpose |
|---|---:|---|---|
| `JWT_SECRET_KEY` | Yes | None | JWT signing and verification secret |
| `JWT_EXPIRE_MINUTES` | No | `60` | JWT lifetime |
| `PORT` | No | `8000` | Backend server port |
| `ALLOWED_ORIGINS` | No | Local Streamlit URLs | Comma-separated CORS allowlist |
| `DATABASE_PATH` | No | `backend/users.db` in local Python; Compose uses `/app/data/users.db` | SQLite database path |
| `AUDIT_LOG_PATH` | No | `logs/audit_log.jsonl` | Audit log path |

### Frontend

| Variable | Required | Default | Purpose |
|---|---:|---|---|
| `FRAUD_API_URL` | Yes for frontend | `http://127.0.0.1:8000` in `.env.example`; Compose uses `http://backend:8000` | FastAPI base URL |
| `COOKIE_PASSWORD` | Yes | None | Encrypted Streamlit cookie key |

`JWT_SECRET_KEY` is required and the backend rejects values shorter than 32 characters. `COOKIE_PASSWORD` is required by the frontend; use a strong unique value. Real secret values must not be committed to Git.

Generate a local JWT secret:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

---

## 20. Local Setup and Execution

### 20.1 Environment file

```powershell
Copy-Item .env.example .env
```

Set:

- `JWT_SECRET_KEY`
- `COOKIE_PASSWORD`
- `FRAUD_API_URL=http://127.0.0.1:8000`

Replace the secret placeholders with strong, unique values. The Docker Compose configuration overrides `FRAUD_API_URL` to `http://backend:8000`.

### 20.2 Backend

Install dependencies:

```powershell
python -m pip install -r backend/requirements.txt
```

Start the API:

```powershell
cd backend
python -m uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

Useful URLs:

- API: `http://127.0.0.1:8000`
- Swagger: `http://127.0.0.1:8000/docs`
- Health: `http://127.0.0.1:8000/health`

### 20.3 Frontend

From the project root:

```powershell
python -m pip install -r frontend/requirements.txt
python -m streamlit run frontend/ui.py
```

Dashboard:

```text
http://localhost:8501
```

### 20.4 Train or refresh the model

```powershell
cd backend
python train_model.py
```

This rewrites:

- `model/xgboost_model.pkl`
- `model/fraud_threshold.pkl`
- `model/shap_explainer.pkl`
- `model/evaluation_metrics.json`
- `model/training_stats.json`

---

## 21. Docker Deployment

### 21.1 Docker Compose

```powershell
docker compose up --build
```

Services:

| Service | Port | Health check |
|---|---:|---|
| `backend` | 8000 | `/health` |
| `frontend` | 8501 | `/_stcore/health` |

Persistent Docker volumes:

- `backend_data`: SQLite database data
- `backend_logs`: audit logs

Stop:

```powershell
docker compose down
```

### 21.2 Backend container

The backend Dockerfile:

- Uses `python:3.11-slim`
- Installs build tools, XGBoost OpenMP runtime, and curl
- Installs backend requirements
- Copies source and model artifacts
- Creates `/app/data` and `/app/logs`
- Exposes port 8000
- Starts Uvicorn

### 21.3 Frontend container

The frontend Dockerfile:

- Uses `python:3.11-slim`
- Installs curl and frontend requirements
- Disables Streamlit usage statistics
- Uses headless server mode
- Exposes port 8501
- Starts `streamlit run ui.py`

---

## 22. Cloud deployment status

AWS deployment is postponed. The local working tree retains experimental App Runner/ECS templates and a manually dispatched workflow; their configured paths are Git-ignored and they are not published. No AWS deployment is claimed as completed or validated. Before any future use, review the workflow, move from long-lived access keys to OIDC, validate task/service configuration, and design durable database/log storage.

GCP deployment is not implemented. See [DEPLOYMENT.md](DEPLOYMENT.md) for the supported local Docker Compose instructions and AWS limitations.

---

## 23. CI/CD Workflows

### CI workflow

[.github/workflows/ci.yml](.github/workflows/ci.yml) triggers on:

- Pushes to `main` or `master`
- Pull requests targeting `main` or `master`
- Manual dispatch

Jobs:

1. Set up Python 3.11.
2. Install backend and development dependencies.
3. Run strict Flake8 checks for syntax and undefined names.
4. Run pytest.
5. Upload test results.
6. Build both Docker images.

### CD workflow

The local-only `.github/workflows/cd-aws.yml` is Git-ignored and will not be available in a public checkout. When retained locally, it has no push trigger and requires an explicit manual opt-in on `main`; it is experimental and not deployment-validated.

It can:

1. Authenticate to AWS using repository access-key secrets (migrate to OIDC before enabling).
2. Log in to Amazon ECR.
3. Build and push backend and frontend images.
4. Tag images with Git SHA and `latest`.
5. Start App Runner deployments.
6. Render and deploy ECS task definitions.

The deployment target supports:

- `apprunner`
- `ecs`
- `ecr_only`

---

## 24. Development Container

[.devcontainer/devcontainer.json](.devcontainer/devcontainer.json) uses:

- Microsoft Python 3.11 Bookworm image
- VS Code Python/Pylance extensions
- Automatic Streamlit startup
- Port 8501 forwarding
- Open-preview behavior

---

## 25. Small Implementation Details

- Database table creation runs on backend startup.
- XGBoost and the threshold are loaded through cache decorators.
- `lru_cache()` means the model and threshold stay in memory once loaded.
- `/predict` returns a Python list of dictionaries.
- `/predict_pdf` catches broad exceptions and returns `{"error": str(e)}`.
- `/predict_live` catches broad exceptions and also returns `{"error": str(e)}` instead of raising HTTP status errors.
- CSV uploads reject the wrong file suffix, but content type is not deeply validated.
- CSV and PDF routes do not persist uploaded transaction data to SQLite.
- Real-time routes persist only after successful prediction.
- PDF routes do not persist parsed transactions to SQLite.
- The frontend intentionally restarts login UI if no token exists.
- The frontend cookie stores the JWT, while Streamlit session state duplicates it.
- The frontend token is sent as `Authorization: Bearer <token>`.
- `/predict`, `/predict_live`, and `/predict_pdf` require a valid Bearer token through `verify_token`.
- The PDF route generates random risk, geo-velocity, and hour values.
- The `new_payee` field is detected only in PDF parsing and is not part of the ML feature contract.
- Merchant risk is random for PDF statements in the current implementation.
- Low-amount PDF transactions are overridden below ₹50 regardless of model output.
- Location is accepted in real-time requests but removed before model inference.
- IP address is obtained from `request.client.host`.
- Device field is populated from the HTTP `User-Agent` header.
- `/predict` has local latency measurement for model inference.
- `/predict_live` and `/predict_pdf` do not return inference latency.
- The frontend downloads CSV results from Pandas.
- Matplotlib generates the dashboard charts.
- The app has custom dark-card CSS embedded in `ui.py`.
- The sidebar assistant stores no conversation history.
- The frontend does not verify that login/signup input fields are non-empty before requests.

---

## 26. Limitations and Known Gaps

### Data limitations

- The training dataset is synthetic.
- There are only 993 records.
- Fraud is 46 records, or about 4.63% of the dataset.
- The test split contains only nine fraud records.
- Behavioral features are constant in training data.
- The behavioral features have no meaningful learned variation.
- External and real-world validation are absent.

### Feature limitations

- Live values are more meaningful than CSV/PDF defaults.
- PDF values for merchant risk, geo velocity, and hour are placeholders or random.
- PDF parser support is heuristic and format-specific.
- Location is accepted but not used numerically.
- The model ignores device or new-payee identity beyond current scalar fields.
- The current retraining data has no labels.

### Evaluation limitations

- Perfect or near-perfect reported ROC-AUC and PR-AUC should not be generalized.
- The synthetic dataset may be unusually separable.
- Only one train/validation/test split is used.
- Cross-validation is not implemented.
- No external time-based or geography-based validation is included.
- No drift detection or monitoring is implemented.

### Database limitations

- SQLite is suitable for a prototype, not high-throughput production.
- No foreign key links transactions to users.
- No unique transaction ID exposed as a public API key.
- Password and transaction data have no encryption at rest in application code.
- Runtime database and log files are container-local unless persistent storage is mounted.

### Authentication limitations

- No password-strength validation.
- No account lockout or login rate limiting.
- No refresh token rotation.
- No MFA.
- No password reset flow.
- No audit for login or signup events.
- JWTs are stored in a browser cookie.

### API limitations

- No formal OpenAPI response models are explicitly configured.
- Some endpoints return generic `{"error": ...}` objects.
- Broad exception handlers hide the underlying API status category.
- `model_loader` and threshold loader caching are in memory.
- `/predict_pdf` still does not return a clean per-row merchant field in all branches.

### PDF limitations

- Random values are unsuitable for security decisions.
- PDF extraction depends on text layout and exact phrases.
- `< ₹50` override is a fixed business rule that can differ from model output.
- PDF parsing does not verify whether the merchant is already a known payee for the authenticated user.

### Deployment limitations

- AWS App Runner example secrets require Secrets Manager setup.
- ECS requires cluster and service secrets.
- SQLite cannot be reliably shared across independently scaled containers.
- Audit logs are not centralized.
- EFS or another storage system is not configured for the SQLite database.
- The deployment guide references RDS conceptually but the code has no migration or RDS integration.

---

## 27. Recommended Future Improvements

1. Replace synthetic data with reviewed real or privacy-safe fraud data.
2. Add meaningful historical behavior columns to the training dataset.
3. Create a formal transaction and fraud-review labeling schema.
4. Add database foreign keys and indexed username lookups.
5. Move from SQLite to PostgreSQL or another managed database.
6. Migrate audit logs to CloudWatch, OpenSearch, or a secure log database.
7. Add cross-validation and external holdout testing.
8. Monitor model drift and data drift.
9. Add threshold-recalibration tooling.
10. Train and validate a PDF-specific pipeline from real statement data.
11. Replace random PDF features with deterministic or unavailable-feature handling.
12. Remove or document the low-amount PDF override.
13. Add user consent and data-retention controls.
14. Add password policy and account lockout.
15. Use refreshable sessions or short-lived access tokens.
16. Add rate limiting and abuse protection.
17. Add formal API response models and typed errors.
18. Add integration tests for signup, login, live prediction, PDF, database, and audit behavior.
19. Add row-level PDF merchant and timestamp extraction.
20. Add Kafka or a queue for real-time transaction streaming.
21. Add a feature-store or centralized feature computation service.
22. Add Prometheus or OpenTelemetry metrics.
23. Add role-based access control for analysts and administrators.
24. Use a secret manager for all local/production credentials.
25. Perform security, privacy, and bias reviews before real deployment.

---

## 28. Example User Flow

### CSV flow

```text
Sign up
  -> Login
  -> Receive JWT
  -> Upload CSV
  -> FastAPI validates file and columns
  -> Preprocessing creates nine features
  -> XGBoost predicts probabilities
  -> Tuned threshold produces Legit/Fraud
  -> Streamlit shows cards, chart, table, and download
```

### Real-time flow

```text
Enter amount and transaction details
  -> Backend reads authenticated username
  -> Past SQLite transactions create behavioral features
  -> Preprocessing validates data
  -> Model predicts probability
  -> SHAP explains important features
  -> Transaction is stored
  -> Prediction is audit logged
  -> Streamlit shows explanation and risk
```

### PDF flow

```text
Upload Google Pay PDF
  -> pdfplumber extracts text
  -> Regex finds merchants and rupee amounts
  -> Placeholder features fill missing fields
  -> Preprocessing creates nine features
  -> Model predicts each transaction
  -> Amounts below ₹50 are overridden as legitimate
  -> Streamlit summarizes and downloads results
```

---

## 29. Final Assessment

The project is a complete demonstration of an ML-backed fraud-detection application:

- It has a working API and dashboard.
- It includes authentication and persistent user/transaction tables.
- It trains and saves an XGBoost model.
- It tunes and applies a fraud threshold.
- It supports CSV, real-time, simulation, and PDF workflows.
- It provides basic and SHAP explanations.
- It includes audit logging and container deployment.
- It includes CI; AWS templates/workflow are postponed, local-only, and Git-ignored.
- It has unit/API tests and a development-container setup.

The largest remaining gaps are the completeness and realism of the data, the implementation of reviewed fraud labels, production-grade storage and authentication, reliable PDF parsing, and end-to-end behavioral feature data in training.
