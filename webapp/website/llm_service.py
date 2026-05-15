"""
LLM-powered diagnostic assistant using Google Gemini API.
Interprets ML model predictions and generates patient-friendly explanations.
"""

import os
import google.generativeai as genai

# Configure Gemini
_api_key = os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY', '')
if _api_key:
    genai.configure(api_key=_api_key)

SYSTEM_PROMPT = """You are MADI (Medical Analysis & Diagnostics Intelligence), an AI medical assistant. 
Your role is to interpret machine learning model predictions and explain them in patient-friendly language.

Guidelines:
- Explain what the prediction means in simple, non-technical terms
- Provide context about the condition
- Suggest general next steps (e.g., "consult your doctor")
- Be empathetic and reassuring in tone
- When multiple predictions are provided, cross-reference them for a holistic view
- Inputs may be tabular lab values or imaging-based model outputs; adjust explanations accordingly without claiming you "saw" an image unless the inputs describe an image study
- ALWAYS include this disclaimer at the end: "⚠️ This analysis is AI-generated and should not replace professional medical advice. Please consult a healthcare provider for proper diagnosis and treatment."

Format your response with clear sections using markdown:
- **Summary**: Brief one-line takeaway
- **Detailed Analysis**: Explanation of what the results mean
- **Recommendations**: Suggested next steps
- **Disclaimer**: The standard disclaimer above
"""


def is_available() -> bool:
    """Check if the Gemini API is configured and available."""
    return bool(_api_key)


def interpret_prediction(
    disease: str,
    prediction: int,
    input_data: dict = None,
    confidence: float = None,
    display_name: str = None,
) -> str:
    """
    Generate a patient-friendly interpretation of a single model prediction.
    
    Args:
        disease: Name of the disease (e.g., 'kidney', 'heart')
        prediction: Model output (0 = negative class, 1 = positive / risk class)
        input_data: Dictionary of input parameters used for prediction
        confidence: Model confidence percentage if available
        display_name: Human-readable screening name (e.g. "Heart Disease")
    
    Returns:
        Formatted interpretation string
    """
    if not is_available():
        return _fallback_interpretation(disease, prediction, display_name)

    label = display_name or disease.replace('_', ' ').title()

    prompt = f"""Interpret the following medical prediction result:

**Screening / condition**: {label}
**Model output (internal)**: {"Risk or abnormality flagged (positive class)" if prediction == 1 else "No strong risk signal for the positive class (negative)"}
"""
    if confidence is not None:
        prompt += f"**Model Confidence**: {confidence}%\n"

    if input_data:
        prompt += "\n**Patient Parameters Used**:\n"
        for key, value in input_data.items():
            prompt += f"- {key}: {value}\n"

    try:
        model = genai.GenerativeModel(
            'gemini-2.0-flash',
            system_instruction=SYSTEM_PROMPT
        )
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Gemini API error: {e}")
        return _fallback_interpretation(disease, prediction, display_name)


def interpret_multiple_predictions(predictions: list) -> str:
    """
    Generate a comprehensive interpretation from multiple model predictions.
    
    Args:
        predictions: List of dicts with keys: disease, prediction, input_data, confidence
    
    Returns:
        Formatted comprehensive interpretation string
    """
    if not is_available():
        return _fallback_multiple(predictions)

    prompt = "Provide a comprehensive analysis of the following multiple medical screening results for a single patient:\n\n"

    for i, pred in enumerate(predictions, 1):
        disease = pred.get('disease', 'Unknown')
        label = pred.get('display_name') or disease.replace('_', ' ').title()
        result = pred.get('prediction', 0)
        confidence = pred.get('confidence')

        prompt += f"### Test {i}: {label}\n"
        prompt += f"- **Result**: {'Risk Detected' if result == 1 else 'No Significant Risk'}\n"
        if confidence is not None:
            prompt += f"- **Confidence**: {confidence}%\n"

        input_data = pred.get('input_data', {})
        if input_data:
            prompt += "- **Parameters**:\n"
            for key, value in input_data.items():
                prompt += f"  - {key}: {value}\n"
        prompt += "\n"

    prompt += "\nPlease provide a holistic analysis considering all test results together, noting any correlations or compounding risk factors."

    try:
        model = genai.GenerativeModel(
            'gemini-2.0-flash',
            system_instruction=SYSTEM_PROMPT
        )
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Gemini API error: {e}")
        return _fallback_multiple(predictions)


def chat_response(message: str, context: str = "") -> str:
    """
    Generate a chat response for follow-up questions.
    
    Args:
        message: User's question
        context: Previous prediction context
    
    Returns:
        Chat response string
    """
    if not is_available():
        return "The AI assistant is currently unavailable. Please ensure the GEMINI_API_KEY is configured."

    prompt = ""
    if context:
        prompt += f"Previous medical screening context:\n{context}\n\n"
    prompt += f"Patient's question: {message}"

    try:
        model = genai.GenerativeModel(
            'gemini-2.0-flash',
            system_instruction=SYSTEM_PROMPT
        )
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Gemini API error: {e}")
        return "I'm sorry, I encountered an error processing your question. Please try again."


def _fallback_interpretation(disease: str, prediction: int, display_name: str = None) -> str:
    """Fallback interpretation when LLM is unavailable."""
    label = display_name or disease.replace('_', ' ').title()
    if prediction == 1:
        return f"""**Summary**: The screening model has detected potential risk indicators related to {label}.

**Detailed Analysis**: Based on the inputs you provided, our machine learning model has identified patterns that are consistent with elevated risk for this screening target. This does not mean you definitely have this condition — it means further investigation may be appropriate.

**Recommendations**:
- Schedule an appointment with your healthcare provider
- Bring these screening results to your consultation
- Follow your doctor's advice for additional diagnostic tests

⚠️ This analysis is AI-generated and should not replace professional medical advice. Please consult a healthcare provider for proper diagnosis and treatment."""
    else:
        return f"""**Summary**: The screening model did not detect a strong positive risk signal for {label}.

**Detailed Analysis**: Based on the inputs you provided, our machine learning model did not flag the positive risk class for this screening. This is encouraging, but no screening tool is 100% accurate.

**Recommendations**:
- Continue maintaining a healthy lifestyle
- Schedule regular check-ups with your healthcare provider
- If you experience any concerning symptoms, seek medical attention promptly

⚠️ This analysis is AI-generated and should not replace professional medical advice. Please consult a healthcare provider for proper diagnosis and treatment."""


def _fallback_multiple(predictions: list) -> str:
    """Fallback for multiple predictions when LLM is unavailable."""
    risk_labels = [
        (p.get('display_name') or p.get('disease', '?').replace('_', ' ').title())
        for p in predictions
        if p.get('prediction') == 1
    ]
    clear_labels = [
        (p.get('display_name') or p.get('disease', '?').replace('_', ' ').title())
        for p in predictions
        if p.get('prediction') == 0
    ]

    result = "**Comprehensive Screening Summary**\n\n"

    if risk_labels:
        result += f"⚠️ **Risk detected** for: {', '.join(risk_labels)}\n\n"
    if clear_labels:
        result += f"✅ **No strong positive signal** for: {', '.join(clear_labels)}\n\n"

    result += "**Recommendations**: Please consult with your healthcare provider to discuss these results and determine appropriate next steps.\n\n"
    result += "⚠️ This analysis is AI-generated and should not replace professional medical advice. Please consult a healthcare provider for proper diagnosis and treatment."

    return result
