"""
run.py — SentimentPro Flask Application Entry Point
MCA Final Year Project
Run: python run.py
Access: http://127.0.0.1:5000
Admin: admin / Admin@123
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import json
from flask import Flask, render_template, session
from app.models.database import get_db, close_db, init_db
from app.routes.auth  import auth_bp
from app.routes.user  import user_bp
from app.routes.admin import admin_bp
from app.utils.sentiment_engine import load_model

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = 'sentimentpro_mca_2024_secure_key_xyz987'
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(user_bp)
app.register_blueprint(admin_bp)

# DB teardown
app.teardown_appcontext(close_db)


# Jinja2 filters
@app.template_filter('from_json')
def from_json(s):
    try: return json.loads(s) if s else []
    except: return []

@app.template_filter('sentiment_emoji')
def sentiment_emoji(s):
    return {'positive':'😊','negative':'😞','neutral':'😐','mixed':'🔀'}.get(s,'😐')

@app.template_filter('sentiment_class')
def sentiment_class(s):
    return {'positive':'pos','negative':'neg','neutral':'neu','mixed':'mix'}.get(s,'neu')


@app.errorhandler(404)
def not_found(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('errors/500.html'), 500


if __name__ == '__main__':
    print("=" * 55)
    print("  SentimentPro — MCA Final Year Project")
    print("  Initialising database…")
    with app.app_context():
        init_db()
    print("  Training ML model…")
    with app.app_context():
        load_model()
    print("  Server starting at http://127.0.0.1:5000")
    print("  Admin credentials: admin / Admin@123")
    print("=" * 55)
    app.run(debug=True, port=5000)
