from flask import Flask, request, render_template, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail,Message
from dotenv import load_dotenv
from flask_cors import CORS
import google.generativeai as genai
import os
import json

# === Load .env ===
load_dotenv()

# === Flask App Config ===
app = Flask(__name__)
app.secret_key = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chatbot.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# ✅ Initialize SQLAlchemy only once
db = SQLAlchemy(app)

# ✅ Initialize CORS
CORS(app, supports_credentials=True)

# ✅ Remove the duplicate db = SQLAlchemy(app) line

# === Mail Config ===
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME')
mail = Mail(app)



# === Gemini AI Setup ===
genai.configure(api_key="AIzaSyAzsMfSo_LqpnwI6eBcxgW1ZbnCGcXfnDA")
model = genai.GenerativeModel('gemini-2.0-flash-exp')

# === Models ===
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    name = db.Column(db.String(120), nullable=False)  # ✅ added

class QuestionLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120))
    question = db.Column(db.Text)
    answer = db.Column(db.Text)
    is_faq = db.Column(db.Boolean, default=False)

# === Load Static FAQs ===
def load_faqs():
    with open(os.path.join('data', 'faqs.json'), 'r', encoding='utf-8') as f:
        return json.load(f)["faqs"]

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
    name = data.get('name')

    if not all([email, password, name]):
        return jsonify({'status': 'fail', 'message': 'Thiếu thông tin đăng ký'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'status': 'exists', 'message': 'Email đã tồn tại'})

    hashed_pw = generate_password_hash(password)
    new_user = User(email=email, password_hash=hashed_pw, name=name)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'status': 'success'})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email).first()
    if user and check_password_hash(user.password_hash, password):
        session['user_email'] = email
        return jsonify({'status': 'success'})
    return jsonify({'status': 'fail', 'message': 'Sai email hoặc mật khẩu'})

@app.route('/api/ask', methods=['POST'])
def ask():
    data = request.get_json()
    question = data.get('question', '').strip().lower()
    email = session.get('user_email', 'guest')
    answer = None
    is_faq = False

    # Static FAQ Match
    for faq in faqs:
        if isinstance(faq, dict):
            faq_question = faq.get('question', '')
            if question in faq_question.lower():
                answer = faq.get('answer', 'Không có câu trả lời.').replace('*', '<br>')
                is_faq = True
                break

    # AI fallback
    if not answer:
        prompt = (
            "Bạn là một trợ lý hữu ích cho dịch vụ tuyển sinh Swinburne Việt Nam. "
            "Nếu không chắc chắn câu trả lời, hãy nói rằng bạn sẽ liên hệ với bộ phận tuyển sinh. "
            f"Câu hỏi: {question}"
        )
        response = model.generate_content(prompt)
        answer = response.text.replace('*', '<br>')

    # Save Q&A to database
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

@app.route('/api/contact-admin', methods=['POST'])
def contact_admin():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    message = data.get('message')

    body = f"""
    📬 Yêu cầu tư vấn mới:

    👤 Họ tên: {name}
    📧 Email: {email}
    📝 Nội dung:
    {message}
    """

    try:
        msg = Message(subject="Liên hệ tư vấn từ người dùng",
                      recipients=[os.getenv('ADMIN_RECEIVER')],
                      body=body)
        mail.send(msg)
        return jsonify({'success': True}), 200
    except Exception as e:
        print("❌ Lỗi gửi mail:", e)
        return jsonify({'error': 'Gửi email thất bại'}), 500

# === Main ===
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    print("✅ Flask server running on http://localhost:5000")
    app.run(debug=True)
