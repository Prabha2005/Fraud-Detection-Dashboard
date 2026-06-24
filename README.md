# Real-Time UPI Fraud Detection System

## Overview

The Real-Time UPI Fraud Detection System is an AI-powered application designed to detect fraudulent UPI transactions in real time. The system uses machine learning techniques to analyze transaction patterns and classify transactions as legitimate or fraudulent, helping improve digital payment security.

The project integrates a trained XGBoost machine learning model with FastAPI-based REST APIs and a Streamlit dashboard for real-time predictions and monitoring.

---

## Live Demo

🚀 Try the application here:

**Fraud Detection Dashboard:**
https://fraud-detection-dashboard-a2ewk5y6yoo6mlw5z995dw.streamlit.app/

---

## Features

* Real-time UPI fraud detection
* Machine learning-powered prediction engine
* FastAPI REST API integration
* Interactive Streamlit dashboard
* Transaction monitoring and visualization
* Data preprocessing and feature engineering pipeline
* Fraud probability scoring
* Scalable deployment architecture

---

## Tech Stack

### Machine Learning

* Python
* XGBoost
* Scikit-Learn
* Pandas
* NumPy

### Backend

* FastAPI
* REST APIs
* Uvicorn

### Frontend & Dashboard

* Streamlit

### Data Processing

* Feature Engineering
* Data Preprocessing
* Class Imbalance Handling (SMOTE)

---

## Project Architecture

```text
Transaction Data
        │
        ▼
Data Preprocessing
        │
        ▼
Feature Engineering
        │
        ▼
XGBoost Model
        │
        ▼
FastAPI REST API
        │
        ▼
Streamlit Dashboard
        │
        ▼
Fraud Prediction Result
```

---

## Dataset

The project uses a synthetic UPI transaction dataset containing approximately 100,000 transaction records.

### Sample Features

* Transaction Amount
* Transaction Type
* Account Balance
* Merchant Information
* Transaction Time
* User Behaviour Patterns
* Fraud Label

---

## Machine Learning Pipeline

### Data Preprocessing

* Missing value handling
* Feature encoding
* Data normalization
* Outlier analysis

### Feature Engineering

* Transaction behavior patterns
* Amount-based indicators
* Time-based features
* Account activity metrics

### Class Imbalance Handling

Fraudulent transactions are significantly fewer than legitimate transactions.

To address this:

* SMOTE (Synthetic Minority Oversampling Technique)
* Stratified train-test split

---

## Model Training

### Algorithm Used

XGBoost Classifier

### Train-Test Split

* Training Data: 80%
* Testing Data: 20%

### Evaluation Metrics

* Accuracy: 94%
* Precision: 90%
* Recall: 93%
* F1-Score: 91%
* AUC-ROC: 0.96

---

## API Endpoints

### Health Check

```http
GET /health
```

### Fraud Prediction

```http
POST /predict
```

Request Example:

```json
{
  "amount": 2500,
  "transaction_type": "UPI",
  "merchant": "Online Store"
}
```

Response Example:

```json
{
  "prediction": "Fraudulent",
  "fraud_probability": 0.92
}
```

---

## Dashboard Features

* Live fraud predictions
* Transaction analytics
* Fraud probability visualization
* Model performance metrics
* Real-time monitoring interface

---

## Results

The trained model successfully detects suspicious transactions with high accuracy and low latency.

### Performance

* Prediction Accuracy: 94%
* Average Inference Time: 87 ms
* AUC-ROC Score: 0.96
* Low False Positive Rate

---

## Future Enhancements

* Integration with live banking APIs
* Deep learning-based fraud detection
* Real-time streaming using Kafka
* User risk profiling
* Explainable AI (XAI) for fraud predictions
* Cloud deployment and monitoring

---

## Learning Outcomes

Through this project, I gained hands-on experience in:

* Machine Learning Model Development
* Fraud Detection Systems
* Data Preprocessing
* Feature Engineering
* FastAPI Development
* REST API Integration
* Streamlit Dashboard Development
* Model Deployment
* End-to-End AI Application Development
