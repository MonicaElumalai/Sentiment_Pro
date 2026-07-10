# SentimentPro — MCA Final Year Project

AI-powered Sentiment Analysis Web Application built with Python Flask.

## Quick Start

```bash
pip install flask werkzeug scikit-learn pandas numpy
python run.py
```

Open: http://127.0.0.1:5000

## Credentials

| Role  | Username | Password  |
|-------|----------|-----------|
| Admin | admin    | Admin@123 |
| User  | Register at /register |

## Features

### Core ML
- TF-IDF + Logistic Regression (90%+ accuracy)
- Aspect-Based Sentiment Analysis (ABSA)
- Mixed sentiment detection
- Lexicon fallback for short clauses

### Modules
- Real-time analysis with AJAX
- Bulk CSV upload & analysis
- Word cloud visualization
- 14-day trend charts
- Search, filter & paginate history
- Export results as CSV
- Dark mode toggle

### Architecture
```
sentimentpro/
├── run.py                    # Entry point
├── app/
│   ├── routes/               # auth, user, admin blueprints
│   ├── models/               # database.py
│   └── utils/                # sentiment_engine.py
├── templates/                # Jinja2 HTML templates
├── static/css/ & js/         # Styles and scripts
├── dataset/reviews.csv       # Training data (240 samples)
└── trained_models/           # Saved ML model
```

## Project Structure

| File | Purpose |
|------|---------|
| `run.py` | Flask app factory, registers blueprints |
| `app/utils/sentiment_engine.py` | ML + ABSA engine |
| `app/models/database.py` | SQLite schema + helpers |
| `app/routes/auth.py` | Login/register/logout |
| `app/routes/user.py` | User dashboard, analyze, history |
| `app/routes/admin.py` | Admin panel, user/review management |
| `static/css/main.css` | Full design system with dark mode |
| `static/js/main.js` | AJAX analysis, charts, word cloud |
