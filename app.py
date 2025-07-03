from flask import Flask, request, render_template, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import google.generativeai as genai
import os
import json

# === App Configuration ===
app = Flask(__name__)
app.secret_key = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chatbot.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# === Gemini API Setup ===
genai.configure(api_key="")
model = genai.GenerativeModel('gemini-2.0-flash-exp')

# === Database Models ===
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

class QuestionLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120))
    question = db.Column(db.Text)
    answer = db.Column(db.Text)
    is_faq = db.Column(db.Boolean, default=False)

# === Load FAQs ===
def load_faqs():
    try:
        with open(os.path.join('data', 'faqs.json'), 'r', encoding='utf-8') as f:
            return json.load(f).get("faqs", [])
    except Exception as e:
        print("Failed to load FAQs:", e)
        return []

faqs = load_faqs()

# === Routes ===
@app.route('/')
def index():
    return render_template('test.html')

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'status': 'fail', 'message': 'Missing fields'})

    if User.query.filter_by(email=email).first():
        return jsonify({'status': 'exists', 'message': 'Email already registered'})

    hashed = generate_password_hash(password)
    new_user = User(email=email, password_hash=hashed)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'status': 'registered'})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email).first()
    if user and check_password_hash(user.password_hash, password):
        session['user_email'] = email
        return jsonify({'status': 'success'})
    return jsonify({'status': 'fail', 'message': 'Invalid credentials'})

@app.route('/api/ask', methods=['POST'])
def ask():
    data = request.get_json()
    question = data.get('question', '').strip().lower()
    email = session.get('user_email', 'guest')
    answer = None
    is_faq = False

    for faq in faqs:
        if isinstance(faq, dict):
            faq_question = faq.get('question', '').lower()
            if question in faq_question:
                answer = faq.get('answer', 'No answer available.').replace('*', '<br>')
                is_faq = True
                break

    if not answer:
        prompt = (
            "You are a helpful assistant for Swinburne VietNam Admission Service. "
            "If you don't know the answer, say you will contact the HQ team (in Vietnamese). "
            f"User question: {question}"
        )
        response = model.generate_content(prompt)
        answer = response.text.replace('*', '<br>')

    log = QuestionLog(email=email, question=question, answer=answer, is_faq=is_faq)
    db.session.add(log)
    db.session.commit()

    return jsonify({'answer': answer})

@app.route('/api/save_unanswered', methods=['POST'])
def save_unanswered():
    data = request.get_json()
    question = data.get('question')
    email = session.get('user_email', 'guest')
    log = QuestionLog(email=email, question=question, answer='', is_faq=False)
    db.session.add(log)
    db.session.commit()
    return jsonify({'status': 'saved'})

# === Run Server ===
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    print("✅ Flask server running with database support...")
    app.run(debug=True)
