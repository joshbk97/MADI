from flask import Blueprint, render_template, redirect, url_for, jsonify, request
from flask_login import login_required, current_user
from .session_manager import get_all_predictions, clear_predictions
from .llm_service import interpret_multiple_predictions, is_available as llm_available

views = Blueprint('views', __name__)


@views.route('/')
def home():
    return render_template('base.html', user=current_user)


@views.route('/kidney')
@login_required
def kidney():
    return render_template('kidney_index.html', user=current_user)


@views.route('/kidney_form')
@login_required
def kidney_form():
    return render_template('kidney.html', user=current_user)


@views.route('/liver')
@login_required
def liver():
    return render_template('liver_index.html', user=current_user)


@views.route('/liver_form')
@login_required
def liver_form():
    return render_template('liver.html', user=current_user)


@views.route('/heart')
@login_required
def heart():
    return render_template('heart_index.html', user=current_user)


@views.route('/heart_form')
@login_required
def heart_form():
    return render_template('heart.html', user=current_user)


@views.route('/stroke')
@login_required
def stroke():
    return render_template('stroke_index.html', user=current_user)


@views.route('/stroke_form')
@login_required
def stroke_form():
    return render_template('stroke.html', user=current_user)


@views.route('/diabetes')
@login_required
def diabetes():
    return render_template('diabete_index.html', user=current_user)


@views.route('/diabetes_form')
@login_required
def diabetes_form():
    return render_template('diabete.html', user=current_user)


@views.route('/pneumonia')
@login_required
def pneumonia():
    return render_template('pneumonia_index.html', user=current_user)


@views.route('/pneumonia_form')
@login_required
def pneumonia_form():
    return render_template('pneumonia.html', user=current_user)


@views.route('/dashboard')
@login_required
def dashboard():
    predictions = get_all_predictions()
    return render_template('dashboard.html', predictions=predictions, 
                         user=current_user, llm_available=llm_available())


@views.route('/clear-session', methods=['POST'])
@login_required
def clear_session():
    clear_predictions()
    return redirect(url_for('views.dashboard'))


@views.route('/api/aggregate-analysis', methods=['POST'])
@login_required
def aggregate_analysis():
    """Generate analysis from stored predictions; optional subset via JSON body."""
    body = request.get_json(silent=True) or {}
    selected = body.get('diseases')
    all_preds = get_all_predictions()

    if isinstance(selected, list) and selected:
        want = {str(x).strip().lower() for x in selected if x}
        predictions = [p for p in all_preds if p.get('disease', '').lower() in want]
    else:
        predictions = all_preds

    if not predictions:
        return jsonify({'error': 'No predictions to analyze for the current selection.'}), 400

    interpretation = interpret_multiple_predictions(predictions)
    return jsonify({'interpretation': interpretation})