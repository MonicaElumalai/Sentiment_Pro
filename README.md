# 🧠 SentimentPro

### AI-Powered Aspect-Based Sentiment Analysis Web Application

**SentimentPro** is a full-stack AI-powered web application developed as an **MCA Final Year Project**. It analyzes customer reviews, identifies product/service aspects, and determines the sentiment associated with each aspect using a hybrid **Machine Learning + Lexicon-based approach**.

🔗 **Live Demo:** [SentimentPro](https://sentiment-pro-mrtg.onrender.com)

---

## ✨ Overview

Understanding whether a review is positive or negative is useful, but understanding **what the customer likes or dislikes** is even more valuable.

For example:

> *"The camera is excellent, but the battery life is disappointing."*

SentimentPro identifies:

| Aspect          | Sentiment   |
| --------------- | ----------- |
| 📷 Camera       | 😊 Positive |
| 🔋 Battery Life | 😞 Negative |

The application can also identify **mixed sentiment**, calculate confidence scores, visualize sentiment trends, and maintain analysis history.

---

## 🚀 Live Application

### 🌐 Try SentimentPro

**[Open Live Demo →](https://sentiment-pro-mrtg.onrender.com)**

> **Note:** The application is deployed on Render. The free hosting instance may take a short time to wake up after a period of inactivity.

---

# 🎯 Key Features

## 🤖 AI & Machine Learning

* **Aspect-Based Sentiment Analysis (ABSA)**
* TF-IDF text vectorization
* Logistic Regression classification
* Custom sentiment lexicon
* Hybrid ML + rule-based sentiment prediction
* Positive / Negative / Neutral classification
* Mixed sentiment detection
* Confidence score calculation
* Aspect detection using pattern matching
* Low-confidence prediction fallback
* Model persistence using Pickle

---

## 👤 User Features

* User registration
* Secure login/logout
* Password hashing
* Personalized dashboard
* Real-time sentiment analysis
* Review history
* Search analysis history
* Filter results
* Pagination
* CSV export
* Sentiment trend visualization
* Word cloud visualization
* Dark mode

---

## 👑 Admin Features

* Admin authentication
* Admin dashboard
* User management
* Review management
* Sentiment analytics
* Review statistics
* Search and filtering
* Data visualization

---

# 🧪 Example Analysis

### Input

```text
The camera quality is excellent but the battery life is poor.
```

### SentimentPro Analysis

```text
Camera
→ Positive
→ High Confidence

Battery Life
→ Negative
→ High Confidence

Overall
→ Mixed Sentiment
```

This demonstrates the difference between traditional sentiment analysis and **aspect-based sentiment analysis**.

---

# 🏗️ System Architecture

```text
                    ┌─────────────────────┐
                    │       User          │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Flask Web App     │
                    │      Frontend       │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Flask Routes      │
                    │ Auth / User / Admin │
                    └──────────┬──────────┘
                               │
                               ▼
                  ┌─────────────────────────┐
                  │   Sentiment Engine       │
                  │                         │
                  │ Aspect Detection        │
                  │        ↓                │
                  │ Lexicon Analysis        │
                  │        ↓                │
                  │ TF-IDF + Logistic Reg.   │
                  │        ↓                │
                  │ Sentiment Prediction    │
                  └────────────┬────────────┘
                               │
                 ┌─────────────┴─────────────┐
                 ▼                           ▼
       ┌──────────────────┐       ┌──────────────────┐
       │  SQLite Database │       │ Trained ML Model │
       │                  │       │                  │
       │ Users            │       │ sentiment_model  │
       │ Reviews          │       │ .pkl             │
       └──────────────────┘       └──────────────────┘
```

---

# 🧠 Machine Learning Pipeline

```text
Customer Review
       │
       ▼
Text Cleaning
       │
       ▼
Aspect Detection
       │
       ▼
Clause Extraction
       │
       ▼
┌─────────────────────────┐
│ Hybrid Sentiment Engine │
├─────────────────────────┤
│ Lexicon Analysis        │
│          +              │
│ TF-IDF + Logistic Reg.  │
└────────────┬────────────┘
             │
             ▼
Sentiment Classification
             │
             ▼
Confidence Calculation
             │
             ▼
Positive / Negative /
Neutral / Mixed
```

---

# 🛠️ Technology Stack

| Category            | Technology                        |
| ------------------- | --------------------------------- |
| Backend             | Python                            |
| Web Framework       | Flask                             |
| Machine Learning    | Scikit-learn                      |
| NLP                 | TF-IDF                            |
| Classification      | Logistic Regression               |
| Data Processing     | Pandas                            |
| Numerical Computing | NumPy                             |
| Database            | SQLite                            |
| Frontend            | HTML5, CSS3, JavaScript           |
| Visualization       | JavaScript Charts                 |
| Authentication      | Flask Sessions + Password Hashing |
| Model Storage       | Pickle                            |
| Version Control     | Git & GitHub                      |
| Deployment          | Render                            |

---

# 📁 Project Structure

```text
Sentiment_Pro/
│
├── run.py
│
├── app/
│   ├── routes/
│   │   ├── auth.py
│   │   ├── user.py
│   │   └── admin.py
│   │
│   ├── models/
│   │   └── database.py
│   │
│   └── utils/
│       └── sentiment_engine.py
│
├── templates/
│   ├── auth/
│   ├── user/
│   ├── admin/
│   └── errors/
│
├── static/
│   ├── css/
│   │   └── main.css
│   └── js/
│       └── main.js
│
├── database/
│   └── sentimentpro.db
│
├── dataset/
│   └── reviews.csv
│
├── trained_models/
│   └── sentiment_model.pkl
│
├── requirements.txt
├── runtime.txt
└── README.md
```

---

# ⚙️ Installation

## 1. Clone the repository

```bash
git clone https://github.com/MonicaElumalai/Sentiment_Pro.git
```

```bash
cd Sentiment_Pro
```

---

## 2. Create a virtual environment

### Windows

```bash
python -m venv venv
```

```bash
venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv venv
```

```bash
source venv/bin/activate
```

---

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Run the application

```bash
python run.py
```

Open:

```text
http://127.0.0.1:5000
```

---

# 🔐 Authentication

SentimentPro supports two types of users:

### Administrator

```text
Username: admin
Password: Admin@123
```

### Regular User

Users can create their own account through the registration page.

> ⚠️ The administrator credentials above are intended only for local/demo use. Production deployments should use environment variables and secure credentials.

---

# 📊 Core Modules

### 🔐 Authentication Module

Handles:

* Registration
* Login
* Logout
* Password hashing
* Session management
* Role-based access

### 👤 User Module

Provides:

* Sentiment analysis
* Review history
* Search
* Filtering
* Pagination
* CSV export
* Dashboard analytics

### 👑 Admin Module

Provides:

* User management
* Review management
* Analytics
* Sentiment statistics
* Administrative dashboard

### 🧠 Sentiment Engine

The sentiment engine combines:

* Aspect detection
* Sentiment lexicon
* TF-IDF
* Logistic Regression
* Confidence scoring
* Negation handling
* Neutral-marker detection
* Mixed sentiment detection

---

# 📈 Supported Sentiment Categories

SentimentPro supports:

🟢 **Positive**

🔴 **Negative**

🟡 **Neutral**

🟣 **Mixed**

---

# 📦 Dataset

The project includes a review dataset used for model training.

```text
Dataset: reviews.csv
Samples: 240
```

The training pipeline uses:

```text
TF-IDF Vectorizer
        ↓
Logistic Regression
        ↓
Sentiment Classification
```

---

# 🔬 Technical Highlights

Some of the important implementation concepts demonstrated in this project include:

* Flask Blueprints
* MVC-style application organization
* SQLite database integration
* CRUD operations
* Session-based authentication
* Password hashing
* REST-style routes
* AJAX requests
* Machine learning model persistence
* Text preprocessing
* Regular expressions
* Feature extraction
* Classification
* Confidence scoring
* Data visualization
* CSV processing
* Error handling

---

# ☁️ Deployment

The application is deployed using **Render**.

### Production entry point

```bash
gunicorn run:app
```

### Python Version

```text
Python 3.11.9
```

### Build Command

```bash
pip install -r requirements.txt
```

---

# 🧪 Local Development

Recommended environment:

```text
Python 3.11.9
```

Install all dependencies:

```bash
pip install -r requirements.txt
```

Start the development server:

```bash
python run.py
```

---

# 🔮 Future Enhancements

Potential future improvements include:

* [ ] PostgreSQL cloud database
* [ ] REST API documentation using Swagger/OpenAPI
* [ ] JWT authentication
* [ ] Advanced transformer-based ABSA
* [ ] BERT-based sentiment classification
* [ ] Multi-language sentiment analysis
* [ ] Product review scraping
* [ ] Real-time analytics dashboard
* [ ] Docker containerization
* [ ] Automated CI/CD pipeline
* [ ] Cloud-based model storage
* [ ] Advanced recommendation system

---

# 👩‍💻 Developer

### Monica E

**MCA | Java Full Stack Developer Aspirant**

Interested in:

* Java
* Spring Boot
* React.js
* Python
* Machine Learning
* Web Development

---

# ⭐ Project Highlights

> **SentimentPro demonstrates the integration of Machine Learning, Natural Language Processing, backend development, database management, frontend development and cloud deployment in a single application.**

### Technologies demonstrated

```text
Python
Flask
Scikit-learn
Pandas
NumPy
SQLite
HTML
CSS
JavaScript
Git
GitHub
Render
```

---

# 📄 License

This project was developed as an **MCA Final Year Academic Project**.

© 2026 Monica E. All rights reserved.
