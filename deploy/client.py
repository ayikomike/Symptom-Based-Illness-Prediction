# Author details
# Mike Ayiko
# 20241201555


import requests
import json
import pandas as pd
import numpy as np


# Configuration
# Base URL of the API (adjust to your deployment)
BASE_URL = "https://illness.predictions.api.yukuvillage.com"  # 
# Or local: "http://localhost:5000"

# Endpoints
MLP_ENDPOINT = f"{BASE_URL}/predict_mlp"
XGB_ENDPOINT = f"{BASE_URL}/predict_xgboost"
ALL_ENDPOINT = f"{BASE_URL}/predict_all"

# Optionally, load the feature columns if you have them saved
# This helps to know which symptom names are expected, but not required.
try:
    import joblib
    feature_cols = joblib.load("saved_models/feature_columns.pkl")
    print(f"Loaded {len(feature_cols)} feature columns.")
except:
    # If not available, we can still send dicts; server will handle missing keys
    feature_cols = None
    print("Warning: feature_columns.pkl not found; you can still send symptom dicts.")


# Helper: create a valid instance dict (optional)
def create_instance(symptom_values):
    """
    symptom_values: dict mapping symptom name to presence (1/0) or any numeric.
    Returns a dict with all feature keys if feature_cols is available;
    otherwise returns the input dict as-is.
    """
    if feature_cols is not None:
        # Ensure all feature columns are present; fill missing with 0 (symptom absent)
        instance = {col: symptom_values.get(col, 0) for col in feature_cols}
        return instance
    else:
        return symptom_values


# Send a prediction request to the MLP model
def predict_mlp(instances):
    """
    instances: list of dicts (each with symptom names and values) or a single dict.
    Returns the JSON response from the server.
    """
    if not isinstance(instances, list):
        instances = [instances]
    # Convert each to proper format (if needed)
    processed = [create_instance(i) for i in instances]
    payload = {"instances": processed}
    response = requests.post(MLP_ENDPOINT, json=payload)
    return response.json()

# Send a prediction request to the XGBoost model
def predict_xgboost(instances):
    if not isinstance(instances, list):
        instances = [instances]
    processed = [create_instance(i) for i in instances]
    payload = {"instances": processed}
    response = requests.post(XGB_ENDPOINT, json=payload)
    return response.json()


# Send a prediction request to both models (ensemble)
def predict_all(instances):
    if not isinstance(instances, list):
        instances = [instances]
    processed = [create_instance(i) for i in instances]
    payload = {"instances": processed}
    response = requests.post(ALL_ENDPOINT, json=payload)
    return response.json()


# Example usage
if __name__ == "__main__":
    # Example symptom data: list of dictionaries with symptom presence (1/0)
    # Only include symptoms that are present; missing ones default to 0 on the server.
    symptom_instances = [
        # Fungal infection
        # {
        #     "itching": 1,
        #     "skin_rash": 1,
        #     "nodal_skin_eruptions": 1
        # },
        # Allergy
        {
            "continuous_sneezing": 1,
            "shivering": 1,
            "chills": 1
        },
        # # GERD
        # {
        #     "stomach_pain": 1,
        #     "acidity": 1,
        #     "ulcers_on_tongue": 1,
        #     "vomiting": 1,
        #     "cough": 1,
        #     "chest_pain": 1
        # },
        # # Chronic cholestasis
        # {
        #     "itching": 1,
        #     "vomiting": 1,
        #     "yellowish_skin": 1,
        #     "nausea": 1,
        #     "loss_of_appetite": 1,
        #     "abdominal_pain": 1,
        #     "yellowing_of_eyes": 1
        # },
        # # Drug Reaction
        # {
        #     "itching": 1,
        #     "skin_rash": 1,
        #     "stomach_pain": 1,
        #     "burning_micturition": 1,
        #     "spotting_ urination": 1
        # }
    ]

    # Predict using MLP
    print("=== MLP Predictions ===")
    result_mlp = predict_mlp(symptom_instances)
    print(json.dumps(result_mlp, indent=2))

    # Predict using XGBoost
    print("\n=== XGBoost Predictions ===")
    result_xgb = predict_xgboost(symptom_instances)
    print(json.dumps(result_xgb, indent=2))

    # Predict using both
    print("\n=== Combined Predictions ===")
    result_all = predict_all(symptom_instances)
    print(json.dumps(result_all, indent=2))

   