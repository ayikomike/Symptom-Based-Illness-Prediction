import os
import sys
import traceback
import pickle
import numpy as np
import pandas as pd
from flask import Flask, request, jsonify
from flask_cors import CORS
import tensorflow as tf
from tensorflow import keras
from sklearn.preprocessing import LabelEncoder
import xgboost as xgb


# Configuration
MODEL_DIR = "/mnt/yukuvillage/adriko/home/ml/illness_predictions/mike_illness_predictions_ms_thesis/deploy/saved_models"   # directory containing all saved artifacts
# If you have a different path, set environment variable or change this line.
# MODEL_DIR = os.environ.get("MODEL_DIR", "saved_models")

# Load artifacts
def load_artifacts():
    """Load label encoders, feature columns, MLP model, and XGBoost model."""
    try:
        # Feature columns (same for both models)
        with open(f"{MODEL_DIR}/feature_columns.pkl", "rb") as f:
            feature_cols = pickle.load(f)
        print(f"Loaded {len(feature_cols)} feature columns.")

        # Label encoder (MLP)
        with open(f"{MODEL_DIR}/label_encoder.pkl", "rb") as f:
            le_mlp = pickle.load(f)

        # Label encoder (traditional)
        with open(f"{MODEL_DIR}/label_encoder_traditional.pkl", "rb") as f:
            le_trad = pickle.load(f)

        # MLP model (Keras)
        mlp_model = keras.models.load_model(f"{MODEL_DIR}/best_mlp_model.h5")
        print("MLP model loaded.")

        # Traditional model (XGBoost)
        with open(f"{MODEL_DIR}/best_traditional_model.pkl", "rb") as f:
            xgb_model = pickle.load(f)
        print("XGBoost model loaded.")

        return feature_cols, le_mlp, le_trad, mlp_model, xgb_model
    except Exception as e:
        print(f"Error loading artifacts: {e}")
        traceback.print_exc()
        sys.exit(1)

feature_cols, le_mlp, le_trad, mlp_model, xgb_model = load_artifacts()
num_classes = len(le_mlp.classes_)


# Preprocessing helper
def preprocess_instances(instances, feature_cols):
    """
    Convert list of symptom dictionaries to DataFrame, fill missing features with 0,
    and return numpy array in the correct column order.
    """
    df = pd.DataFrame(instances)
    # Ensure all feature columns exist; missing ones get NaN (will be filled with 0)
    for col in feature_cols:
        if col not in df.columns:
            df[col] = np.nan
    # Keep only feature columns in the defined order
    df = df[feature_cols]
    # Replace NaN with 0 (symptom absent)
    df = df.fillna(0)
    return df.values.astype(np.float32)


# Flask app
app = Flask(__name__)
CORS(app)   # Enable CORS for cross-origin requests

@app.route('/', methods=['GET'])
def index():
    return """
    <h2>Symptom‑Based Disease Prediction API</h2>
    <p>POST to one of the following endpoints with JSON:</p>
    <pre>
    {
      "instances": [
        {"symptom_1": 1, "symptom_2": 0, ...},
        ...
      ]
    }
    </pre>
    <ul>
      <li><code>/predict_mlp</code> – uses deep learning MLP</li>
      <li><code>/predict_xgboost</code> – uses XGBoost (traditional)</li>
      <li><code>/predict_all</code> – returns both predictions</li>
    </ul>
    <p>Each instance must contain <strong>all</strong> symptom features; missing ones default to 0.</p>
    """

@app.route('/predict_mlp', methods=['POST'])
def predict_mlp():
    try:
        data = request.get_json()
        if not data or 'instances' not in data:
            return jsonify({'error': 'Missing "instances" key'}), 400
        instances = data['instances']
        if not isinstance(instances, list) or len(instances) == 0:
            return jsonify({'error': '"instances" must be a non‑empty list'}), 400

        X = preprocess_instances(instances, feature_cols)

        # Get probabilities
        probs = mlp_model.predict(X)  # shape (n, num_classes)
        pred_indices = np.argmax(probs, axis=1)
        pred_diseases = le_mlp.inverse_transform(pred_indices)
        confidences = np.max(probs, axis=1)

        results = []
        for i in range(len(instances)):
            results.append({
                "instance": instances[i],
                "predicted_disease": pred_diseases[i],
                "confidence": round(float(confidences[i]), 4),
                # Optionally include all class probabilities
                # "probabilities": {le_mlp.classes_[j]: round(float(probs[i, j]), 4) for j in range(num_classes)}
            })
        return jsonify({"predictions": results})

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/predict_xgboost', methods=['POST'])
def predict_xgboost():
    try:
        data = request.get_json()
        if not data or 'instances' not in data:
            return jsonify({'error': 'Missing "instances" key'}), 400
        instances = data['instances']
        if not isinstance(instances, list) or len(instances) == 0:
            return jsonify({'error': '"instances" must be a non‑empty list'}), 400

        X = preprocess_instances(instances, feature_cols)

        # XGBoost with multi:softmax supports predict_proba
        probs = xgb_model.predict_proba(X)   # shape (n, num_classes)
        pred_indices = np.argmax(probs, axis=1)
        pred_diseases = le_trad.inverse_transform(pred_indices)
        confidences = np.max(probs, axis=1)

        results = []
        for i in range(len(instances)):
            results.append({
                "instance": instances[i],
                "predicted_disease": pred_diseases[i],
                "confidence": round(float(confidences[i]), 4)
            })
        return jsonify({"predictions": results})

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/predict_all', methods=['POST'])
def predict_all():
    """
    Combines predictions from both models.
    """
    try:
        data = request.get_json()
        if not data or 'instances' not in data:
            return jsonify({'error': 'Missing "instances" key'}), 400
        instances = data['instances']
        if not isinstance(instances, list) or len(instances) == 0:
            return jsonify({'error': '"instances" must be a non‑empty list'}), 400

        X = preprocess_instances(instances, feature_cols)

        # MLP
        probs_mlp = mlp_model.predict(X)
        pred_idx_mlp = np.argmax(probs_mlp, axis=1)
        pred_disease_mlp = le_mlp.inverse_transform(pred_idx_mlp)
        conf_mlp = np.max(probs_mlp, axis=1)

        # XGBoost
        probs_xgb = xgb_model.predict_proba(X)
        pred_idx_xgb = np.argmax(probs_xgb, axis=1)
        pred_disease_xgb = le_trad.inverse_transform(pred_idx_xgb)
        conf_xgb = np.max(probs_xgb, axis=1)

        results = []
        for i in range(len(instances)):
            results.append({
                "instance": instances[i],
                "mlp": {
                    "predicted_disease": pred_disease_mlp[i],
                    "confidence": round(float(conf_mlp[i]), 4)
                },
                "xgboost": {
                    "predicted_disease": pred_disease_xgb[i],
                    "confidence": round(float(conf_xgb[i]), 4)
                }
            })
        return jsonify({"predictions": results})

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# Run the app
if __name__ == '__main__':
    # Use debug=False for production; set host to 0.0.0.0 to listen on all interfaces
    app.run(host='0.0.0.0', port=5000, debug=False)