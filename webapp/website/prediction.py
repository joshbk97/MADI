from typing import Optional

from flask import Blueprint, render_template, request, send_from_directory, jsonify
from flask_login import login_required, current_user
from .app_functions import (
    predict_kidney, predict_liver, predict_heart,
    predict_stroke, predict_diabetes, predict_pneumonia,
    DISEASE_MODELS,
)
from .session_manager import save_prediction
from .llm_service import interpret_prediction, chat_response, is_available as llm_available
import os
from werkzeug.utils import secure_filename

prediction = Blueprint('prediction', __name__)

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')

# Form field order must match training feature order for each tabular model.
KIDNEY_FIELDS = [
    'age', 'blood_pressure', 'Specific_Gravity', 'Blood_Glucose_Random',
    'Blood_Urea', 'Serum_Creatinine', 'Hemoglobin', 'Pus Cell Clumps',
    'Bacteria', 'Hypertension', 'Diabetes Mellitus', 'Coronary Artery Disease',
    'Appetite', 'Pedal Edema', 'Anemia',
]

LIVER_FIELDS = [
    'age', 'Total_Bilirubin', 'Direct_Bilirubin', 'Alkaline_Phosphotase',
    'Alamine_Aminotransferase', 'Aspartate_Aminotransferase', 'Total_Protiens',
    'Albumin', 'Albumin_and_Globulin_Ratio', 'Gender',
]

HEART_FIELDS = [
    'age', 'Gender', 'cp', 'trestbps', 'chol', 'fbs',
    'restecg', 'thalach', 'exang', 'oldpeak', 'slope',
]

STROKE_FIELDS = [
    'age', 'avg_glucose_level', 'hypertension', 'heart_disease',
    'Gender', 'ever_married', 'work_type', 'Residence_type', 'Smoking_status',
]

DIABETES_FIELDS = [
    'pregnancies', 'Glucose', 'blood_pressure', 'BSkinThickness',
    'Insulin', 'BMI', 'DiabetesPedigreeFunction', 'Age',
]

TABULAR_MODEL_FIELDS = {
    'kidney': KIDNEY_FIELDS,
    'liver': LIVER_FIELDS,
    'heart': HEART_FIELDS,
    'stroke': STROKE_FIELDS,
    'diabetes': DIABETES_FIELDS,
}

TABULAR_PREDICTORS = {
    'kidney': predict_kidney,
    'liver': predict_liver,
    'heart': predict_heart,
    'stroke': predict_stroke,
    'diabetes': predict_diabetes,
}


def _extract_form_inputs(form_dict: dict, fields: list) -> tuple:
    """Extract and convert form inputs to float list and labeled dict."""
    values = []
    labeled = {}
    for field in fields:
        val = form_dict.get(field, '0')
        values.append(float(val))
        labeled[field] = val
    return values, labeled


def _guess_tabular_model(form_dict: dict) -> Optional[str]:
    """Infer model from field count (legacy clients without madi_model)."""
    n = len(form_dict)
    for key, meta in DISEASE_MODELS.items():
        nf = meta.get('num_features')
        if nf is not None and nf == n:
            return key
    return None


def _run_tabular(disease: str, form_data: dict) -> tuple:
    fields = TABULAR_MODEL_FIELDS[disease]
    float_values, input_labels = _extract_form_inputs(form_data, fields)
    predict_fn = TABULAR_PREDICTORS[disease]
    return predict_fn(float_values), input_labels


@prediction.route('/predict', methods=['POST', 'GET'])
@login_required
def predict():
    if request.method == 'GET':
        return render_template('base.html', user=current_user)

    form_data = request.form.to_dict()
    model_key = (form_data.pop('madi_model', None) or '').strip().lower()

    if not model_key or model_key not in TABULAR_MODEL_FIELDS:
        model_key = _guess_tabular_model(form_data)

    if not model_key or model_key not in TABULAR_MODEL_FIELDS:
        return render_template(
            'prediction_error.html',
            title='Could not run screening',
            message='Unknown or incomplete form submission. Please use the disease form from the Models section.',
            user=current_user,
        )

    disease = model_key
    model_info = DISEASE_MODELS.get(disease, {})

    try:
        (result, proba), input_labels = _run_tabular(disease, form_data)
    except FileNotFoundError as e:
        return render_template(
            'prediction_error.html',
            title='Model not installed',
            message=str(e),
            user=current_user,
        )
    except Exception as e:
        return render_template(
            'prediction_error.html',
            title='Prediction error',
            message=f'The model could not process your input: {e}',
            user=current_user,
        )

    confidence = None
    if proba is not None:
        try:
            confidence = round(float(max(proba)) * 100, 1)
        except (TypeError, ValueError):
            confidence = None

    save_prediction(
        disease=disease,
        prediction=int(result),
        input_data=input_labels,
        confidence=confidence,
        display_name=model_info.get('display_name', disease.title()),
    )

    return render_template(
        'result.html',
        prediction=int(result),
        page=disease,
        display_name=model_info.get('display_name', disease.title()),
        confidence=confidence,
        model_accuracy=model_info.get('accuracy'),
        input_data=input_labels,
        llm_available=llm_available(),
        user=current_user,
    )


@prediction.route('/upload', methods=['POST', 'GET'])
@login_required
def upload_file():
    if request.method == 'GET':
        return render_template('pneumonia.html', user=current_user)

    file = request.files.get('file')
    if not file or file.filename == '':
        return render_template('pneumonia.html', user=current_user,
                               error='Please select a file to upload.')

    filename = secure_filename(file.filename)
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)

    model_info = DISEASE_MODELS.get('pneumonia', {})

    try:
        result_value, label, confidence = predict_pneumonia(file_path)
    except FileNotFoundError as e:
        return render_template(
            'prediction_error.html',
            title='Model not installed',
            message=str(e),
            user=current_user,
        )
    except Exception as e:
        return render_template('pneumonia.html', user=current_user,
                               error=f'Error processing image: {str(e)}')

    pred_int = 1 if label == 'Pneumonia' else 0

    save_prediction(
        disease='pneumonia',
        prediction=pred_int,
        input_data={'image': filename},
        confidence=confidence,
        display_name=model_info.get('display_name', 'Pneumonia'),
    )

    return render_template(
        'deep_pred.html',
        image_file_name=filename,
        label=label,
        accuracy=confidence,
        prediction=pred_int,
        display_name=model_info.get('display_name', 'Pneumonia'),
        llm_available=llm_available(),
        user=current_user,
    )


@prediction.route('/uploads/<filename>')
@login_required
def send_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


@prediction.route('/api/interpret', methods=['POST'])
@login_required
def api_interpret():
    """Generate LLM interpretation for a prediction."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    disease = data.get('disease', '')
    pred = data.get('prediction', 0)
    input_data = data.get('input_data', {})
    confidence = data.get('confidence')
    display_name = data.get('display_name')

    interpretation = interpret_prediction(
        disease, pred, input_data, confidence, display_name=display_name
    )
    return jsonify({'interpretation': interpretation})


@prediction.route('/api/chat', methods=['POST'])
@login_required
def api_chat():
    """Handle follow-up chat questions."""
    data = request.get_json()
    if not data or not data.get('message'):
        return jsonify({'error': 'No message provided'}), 400

    message = data['message']
    context = data.get('context', '')

    response = chat_response(message, context)
    return jsonify({'response': response})
