from flask import Flask, request, render_template, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail,Message
from dotenv import load_dotenv
from flask_cors import CORS
import google.generativeai as genai
import os
import json
import difflib
from fuzzywuzzy import fuzz

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
    name = db.Column(db.String(120), nullable=False)

class QuestionLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120))
    question = db.Column(db.Text)
    answer = db.Column(db.Text)
    is_faq = db.Column(db.Boolean, default=False)

# === Load Static FAQs ===
def load_faqs():
    try:
        with open(os.path.join('data', 'faqs.json'), 'r', encoding='utf-8') as f:
            return json.load(f)["faqs"]
    except FileNotFoundError:
        print("❌ faqs.json not found, using empty FAQ list")
        return []

faqs = load_faqs()

# === Routes ===
@app.route('/')
def index():
    return render_template('test.html')

# ✅ Fix: Add route to serve FAQ data for frontend
@app.route('/data/faqs.json')
def serve_faqs():
    """Serve FAQ data for frontend autocomplete"""
    return jsonify({"faqs": faqs})

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
    question = data.get('question', '').strip()
    email = session.get('user_email', 'guest')
    answer = None
    is_faq = False
    match_score = 0

    print(f"🔍 User question: {question}")

    # STEP 1: Enhanced FAQ Matching
    best_match = find_best_faq_match(question)
    
    if best_match and best_match['score'] >= 70:  # 70% similarity threshold
        answer = best_match['answer']
        # ✅ Fix: Check if answer exists and is not empty
        if answer and answer.strip():
            answer = answer.replace('*', '<br>')
            is_faq = True
            match_score = best_match['score']
            print(f"✅ FAQ Match: {best_match['score']}% - {best_match['question']}")
            print(f"✅ Using FAQ Answer: {answer[:100]}...")
        else:
            print("⚠️ FAQ matched but answer is empty, using AI fallback")
            answer = None  # Reset to trigger AI fallback
    
    # STEP 2: AI Fallback with Context
    if not answer or not answer.strip():
        print("🤖 Using Gemini AI fallback")
        # Provide FAQ context to AI
        faq_context = "\n".join([f"Q: {faq['question']}\nA: {faq['answer']}" for faq in faqs[:5] if faq.get('answer')])
        
        prompt = f"""
        Bạn là trợ lý tuyển sinh Swinburne Việt Nam. Sử dụng thông tin FAQ sau để trả lời:

        {faq_context}

        Nếu câu hỏi không liên quan đến thông tin trên, hãy nói "Tôi sẽ chuyển cho bộ phận tuyển sinh để được hỗ trợ tốt hơn."

        Câu hỏi: {question}
        """
        
        try:
            response = model.generate_content(prompt)
            answer = response.text.replace('*', '<br>')
            print(f"🤖 AI Response: {answer[:100]}...")
        except Exception as e:
            print(f"❌ AI Error: {e}")
            answer = "Xin lỗi, tôi gặp sự cố kỹ thuật. Vui lòng liên hệ bộ phận tuyển sinh để được hỗ trợ."
    else:
        print("✅ Using FAQ answer, skipping AI")

    # STEP 3: Log with match details
    log = QuestionLog(
        email=email, 
        question=question, 
        answer=answer, 
        is_faq=is_faq
    )
    db.session.add(log)
    db.session.commit()

    return jsonify({
        'answer': answer,
        'is_faq': is_faq,
        'match_score': match_score
    })

def find_best_faq_match(user_question):
    """
    Find the best matching FAQ using multiple similarity algorithms
    """
    if not faqs:
        print("⚠️ No FAQs loaded")
        return None
        
    user_question = user_question.lower().strip()
    best_match = None
    highest_score = 0
    
    print(f"🔍 Searching through {len(faqs)} FAQs...")
    
    for i, faq in enumerate(faqs):
        if not isinstance(faq, dict):
            continue
            
        faq_question = faq.get('question', '').lower().strip()
        faq_answer = faq.get('answer', '').strip()
        
        if not faq_question:
            continue
        
        # Method 1: Fuzzy string matching
        fuzzy_score = fuzz.ratio(user_question, faq_question)
        
        # Method 2: Partial ratio (substring matching)
        partial_score = fuzz.partial_ratio(user_question, faq_question)
        
        # Method 3: Token sort ratio (word order independent)
        token_score = fuzz.token_sort_ratio(user_question, faq_question)
        
        # Method 4: Keyword matching
        user_words = set(user_question.split())
        faq_words = set(faq_question.split())
        common_words = user_words.intersection(faq_words)
        keyword_score = (len(common_words) / len(user_words)) * 100 if user_words else 0
        
        # Combined score (weighted average)
        combined_score = (
            fuzzy_score * 0.3 + 
            partial_score * 0.3 + 
            token_score * 0.2 + 
            keyword_score * 0.2
        )
        
        if combined_score > highest_score:
            highest_score = combined_score
            best_match = {
                'question': faq.get('question', ''),
                'answer': faq_answer,
                'score': round(combined_score, 2)
            }
            print(f"🔍 New best match [{i}]: {combined_score:.1f}% - Answer length: {len(faq_answer)}")
    
    print(f"🏆 Final best match: {highest_score:.1f}%")
    return best_match if highest_score >= 50 else None  # Minimum 50% match

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
                      recipients=[os.getenv('ADMIN_RECEIVER', 'admin@example.com')],
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
    print(f"✅ Loaded {len(faqs)} FAQs")
    app.run(debug=True)