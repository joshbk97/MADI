# MADI — Medical Analysis & Diagnostics Intelligence

MADI is an AI-driven medical diagnostic platform for multi-modal disease prediction and chest X-ray analysis, integrated with Google Gemini for intelligent synthesis.

## Features

*   **Multi-modal Predictive Models**: Specialized ML models for Kidney, Liver, Heart, Stroke, and Diabetes prediction using clinical parameters.
*   **Deep Learning Image Analysis**: CNN-based pneumonia detection from chest X-rays.
*   **AI Diagnostic Assistant**: Integration with Google Gemini API to interpret complex prediction results and generate patient-friendly summaries.
*   **Diagnostic Aggregation**: A unified session dashboard to compile multiple test results and identify compounding risk factors using AI synthesis.
*   **Modern Interface**: A clean, responsive, dark-mode medical-tech aesthetic built with glassmorphism design principles.

## Available Models

| Disease | Model Type | Inputs | Accuracy |
| :--- | :--- | :--- | :--- |
| **Kidney Disease** | Random Forest | 15 clinical indicators | 98% |
| **Liver Disease** | XGBoost | 10 clinical indicators | 84% |
| **Heart Disease** | Random Forest | 11 clinical indicators | 90% |
| **Stroke** | Random Forest | 9 clinical/lifestyle indicators | 95% |
| **Diabetes** | XGBoost | 8 clinical indicators | 86% |
| **Pneumonia** | CNN (Keras/TF) | Chest X-Ray Image | 92% |

## Technology Stack

*   **Backend**: Python, Flask, Flask-Login, Flask-SQLAlchemy
*   **Machine Learning**: Scikit-Learn, TensorFlow/Keras, XGBoost
*   **LLM Integration**: Google Generative AI (Gemini 2.0 Flash)
*   **Frontend**: HTML5, CSS3, Bootstrap 3 (Customized)

## Setup and Installation

### 1. Clone the repository
```bash
git clone https://github.com/joshbk97/MADI.git
cd MADI/webapp
```

### 2. Set up a virtual environment (Recommended)
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy the example environment file and add your Google Gemini API key:
```bash
cp .env.example .env
```
Edit `.env` and add your keys:
```
GEMINI_API_KEY=your_gemini_api_key_here
SECRET_KEY=your_secret_key_here
FLASK_DEBUG=true
```

### 5. Run the application
```bash
python app.py
```
The application will be available at `http://127.0.0.1:5000`.

## Architecture Flow
1. **User Input**: Clinical data is submitted via forms, or X-rays via file upload.
2. **Prediction**: `app_functions.py` routes the data to the appropriate pre-trained `.pkl` or `.h5` model.
3. **Session Storage**: Results are temporarily stored in the Flask session (`session_manager.py`).
4. **AI Interpretation**: `llm_service.py` securely sends the prediction and context to the Gemini API to generate a readable summary.
5. **Aggregation**: The dashboard view allows the LLM to cross-reference multiple disease predictions from the session.

## License
Original layout template adapted from Tooplate (Template 2081 Solution). ML models trained on publicly available Kaggle datasets.
