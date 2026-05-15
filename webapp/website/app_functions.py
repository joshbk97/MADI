"""
ML model loading and prediction functions for MADI.
Each disease model has its own named function for clarity.
Models are cached after first load to avoid reloading on every request.
"""

import pickle
import os
import numpy as np
from functools import lru_cache
from tensorflow.keras.preprocessing.image import load_img
from tensorflow.keras.models import load_model

# Base path for model files
MODELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app_models')


# --- Model Loaders (cached) ---

@lru_cache(maxsize=None)
def _load_pickle_model(filename: str):
    """Load and cache a pickle model file."""
    path = os.path.join(MODELS_DIR, filename)
    if not os.path.isfile(path):
        raise FileNotFoundError(
            f'Model file not found: {path}. Place trained weights (.pkl) in website/app_models/.'
        )
    with open(path, 'rb') as f:
        return pickle.load(f)


@lru_cache(maxsize=None)
def _load_keras_model(filename: str):
    """Load and cache a Keras model file."""
    path = os.path.join(MODELS_DIR, filename)
    if not os.path.isfile(path):
        raise FileNotFoundError(
            f'Model file not found: {path}. Place the Keras model (.h5) in website/app_models/.'
        )
        
    if filename == 'pneumonia_model.h5':
        from tensorflow.keras.applications import MobileNetV2
        from tensorflow.keras.models import Sequential
        from tensorflow.keras.layers import GlobalAveragePooling2D, Dropout, Dense
        import h5py
        
        # Build model dynamically to avoid corrupted H5 architecture parsing
        base_model = MobileNetV2(input_shape=(224, 224, 3), include_top=False, weights=None, name='mobilenetv2_1.00_224')
        model = Sequential([
            base_model,
            GlobalAveragePooling2D(name='global_average_pooling2d'),
            Dropout(0.2, name='dropout'),
            Dense(1, activation='sigmoid', name='dense')
        ])
        
        # Manually load weights to bypass topological mismatches and variable renames (Keras 2 -> 3)
        with h5py.File(path, 'r') as f:
            weight_dict = {}
            def visit_fn(name, node):
                if isinstance(node, h5py.Dataset):
                    weight_dict[name] = node[:]
            f['model_weights'].visititems(visit_fn)
            
            for var in model.variables:
                parts = var.name.split('/')
                suffix = '/' + '/'.join(parts[-2:]) if len(parts) >= 2 else '/' + var.name
                old_suffix = suffix.replace('/kernel:0', '/depthwise_kernel:0')
                
                match_key = None
                for k in weight_dict:
                    k_with_slash = '/' + k
                    if k_with_slash.endswith(suffix) or k_with_slash.endswith(old_suffix):
                        match_key = k
                        break
                
                if match_key:
                    try:
                        var.assign(weight_dict[match_key])
                    except Exception:
                        pass
        return model
        
    from tensorflow.keras.models import load_model
    return load_model(path, compile=False)


# --- Disease-Specific Prediction Functions ---

def predict_kidney(inputs: list) -> tuple:
    """
    Kidney disease prediction.
    Expects 15 input features.
    Returns (prediction_int, probability_or_none).
    """
    model = _load_pickle_model('kidney_model.pkl')
    data = np.array(inputs).reshape(1, -1)
    pred = model.predict(data)[0]
    proba = None
    if hasattr(model, 'predict_proba'):
        proba = model.predict_proba(data)[0]
    return int(pred), proba


def predict_liver(inputs: list) -> tuple:
    """
    Liver disease prediction.
    Expects 10 input features.
    Returns (prediction_int, probability_or_none).
    """
    model = _load_pickle_model('liver_model.pkl')
    data = np.array(inputs).reshape(1, -1)
    pred = model.predict(data)[0]
    proba = None
    if hasattr(model, 'predict_proba'):
        proba = model.predict_proba(data)[0]
    return int(pred), proba


def predict_heart(inputs: list) -> tuple:
    """
    Heart disease prediction.
    Expects 11 input features.
    Returns (prediction_int, probability_or_none).
    """
    model = _load_pickle_model('heart_model.pkl')
    data = np.array(inputs).reshape(1, -1)
    pred = model.predict(data)[0]
    proba = None
    if hasattr(model, 'predict_proba'):
        proba = model.predict_proba(data)[0]
    return int(pred), proba


def predict_stroke(inputs: list) -> tuple:
    """
    Stroke prediction.
    Expects 9 input features. First 2 are scaled separately.
    Returns (prediction_int, probability_or_none).
    """
    scaler = _load_pickle_model('avc_scaler.pkl')
    model = _load_pickle_model('avc_model.pkl')

    # Scale the first 2 features (age, avg_glucose_level)
    scaled = scaler.transform(np.array(inputs[0:2]).reshape(1, -1)).tolist()[0]
    remaining = inputs[2:]
    combined = scaled + remaining

    data = np.array(combined).reshape(1, -1)
    pred = model.predict(data)[0]
    proba = None
    if hasattr(model, 'predict_proba'):
        proba = model.predict_proba(data)[0]
    return int(pred), proba


def predict_diabetes(inputs: list) -> tuple:
    """
    Diabetes prediction.
    Expects 8 input features.
    Returns (prediction_int, probability_or_none).
    """
    model = _load_pickle_model('diabete_model.pkl')
    data = np.array(inputs).reshape(1, -1)
    pred = model.predict(data)[0]
    proba = None
    if hasattr(model, 'predict_proba'):
        proba = model.predict_proba(data)[0]
    return int(pred), proba


def predict_pneumonia(image_path: str) -> tuple:
    """
    Pneumonia prediction from chest X-ray image.
    Uses a Keras CNN model.
    Returns (prediction_float, label_str).
    """
    model = _load_keras_model('pneumonia_model.h5')
    img = load_img(image_path, target_size=(224, 224, 3))
    data = np.asarray(img).reshape(1, 224, 224, 3) / 255.0
    # Manual forward pass to bypass Keras 3 Sequential graph corruption
    x = data
    for layer in model.layers:
        if 'dropout' in layer.name.lower():
            x = layer(x, training=False)
        else:
            x = layer(x)
        if isinstance(x, list):
            x = x[0]

    if hasattr(x, 'numpy'):
        result = x.numpy()[0][0]
    else:
        result = x[0][0]
        
    result = float(np.round(result, 4))

    if result > 0.5:
        label = 'Pneumonia'
        confidence = round(result * 100, 1)
    else:
        label = 'Normal'
        confidence = round((1 - result) * 100, 1)

    return result, label, confidence


# --- Dispatch Map ---

DISEASE_MODELS = {
    'kidney': {
        'predict': predict_kidney,
        'num_features': 15,
        'input_modality': 'tabular',
        'display_name': 'Kidney Disease',
        'accuracy': 98,
    },
    'liver': {
        'predict': predict_liver,
        'num_features': 10,
        'input_modality': 'tabular',
        'display_name': 'Liver Disease',
        'accuracy': 84,
    },
    'heart': {
        'predict': predict_heart,
        'num_features': 11,
        'input_modality': 'tabular',
        'display_name': 'Heart Disease',
        'accuracy': 90,
    },
    'stroke': {
        'predict': predict_stroke,
        'num_features': 9,
        'input_modality': 'tabular',
        'display_name': 'Stroke',
        'accuracy': 95,
    },
    'diabetes': {
        'predict': predict_diabetes,
        'num_features': 8,
        'input_modality': 'tabular',
        'display_name': 'Diabetes',
        'accuracy': 86,
    },
    'pneumonia': {
        'predict': predict_pneumonia,
        'num_features': None,
        'input_modality': 'chest_xray',
        'display_name': 'Pneumonia (Chest X-Ray)',
        'accuracy': 92,
    },
}
