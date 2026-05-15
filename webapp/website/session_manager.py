"""
Session-based prediction history manager.
Stores prediction results in Flask session for multi-model aggregation.
"""

from flask import session
from datetime import datetime


def save_prediction(disease: str, prediction: int, input_data: dict, 
                    confidence: float = None, display_name: str = None):
    """
    Save a prediction result to the user's session.
    
    Args:
        disease: Disease key (e.g., 'kidney')
        prediction: Model output (0 or 1)
        input_data: Dict of input parameters
        confidence: Model confidence if available
        display_name: Human-readable disease name
    """
    if 'predictions' not in session:
        session['predictions'] = []

    entry = {
        'disease': disease,
        'display_name': display_name or disease.title(),
        'prediction': prediction,
        'input_data': input_data,
        'confidence': confidence,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }

    # Replace existing prediction for same disease (keep latest)
    predictions = [p for p in session['predictions'] if p['disease'] != disease]
    predictions.append(entry)
    session['predictions'] = predictions
    session.modified = True


def get_all_predictions() -> list:
    """Get all predictions stored in the current session."""
    return session.get('predictions', [])


def get_prediction(disease: str) -> dict:
    """Get a specific disease prediction from the session."""
    predictions = session.get('predictions', [])
    for p in predictions:
        if p['disease'] == disease:
            return p
    return None


def clear_predictions():
    """Clear all predictions from the session."""
    session.pop('predictions', None)
    session.modified = True


def get_prediction_count() -> int:
    """Get the number of predictions in the current session."""
    return len(session.get('predictions', []))
