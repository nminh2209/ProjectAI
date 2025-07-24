from flask import Flask, request, render_template, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
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

# === Enhanced Models ===
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

class FAQ(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100), default='General')
    keywords = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    priority = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

class QuestionLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120))
    question = db.Column(db.Text)
    answer = db.Column(db.Text)
    is_faq = db.Column(db.Boolean, default=False)
    faq_id = db.Column(db.Integer, db.ForeignKey('faq.id'), nullable=True)
    match_score = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

# === FAQ Management Functions ===
def load_faqs_from_db():
    """Load FAQs from database instead of JSON file"""
    faqs = FAQ.query.filter_by(is_active=True).order_by(FAQ.priority.desc(), FAQ.created_at.desc()).all()
    return [{'id': faq.id, 'question': faq.question, 'answer': faq.answer, 'category': faq.category, 'keywords': faq.keywords} for faq in faqs]

def migrate_json_to_db():
    """One-time migration from JSON to database"""
    try:
        with open(os.path.join('data', 'faqs.json'), 'r', encoding='utf-8') as f:
            json_faqs = json.load(f)["faqs"]
            
        for faq_data in json_faqs:
            existing = FAQ.query.filter_by(question=faq_data.get('question')).first()
            if not existing:
                new_faq = FAQ(
                    question=faq_data.get('question', ''),
                    answer=faq_data.get('answer', ''),
                    category=faq_data.get('category', 'General')
                )
                db.session.add(new_faq)
        
        db.session.commit()
        print(f"✅ Migrated {len(json_faqs)} FAQs to database")
    except FileNotFoundError:
        print("📝 No JSON file found, starting with empty FAQ database")

# Load FAQs from database
faqs = []

# === Routes ===
@app.route('/')
def index():
    return render_template('test.html')

@app.route('/admin')
def admin_panel():
    if not session.get('is_admin'):
        return render_template('admin_login.html')
    return render_template('admin_panel.html')

# ✅ Fix: Add route to serve FAQ data for frontend
@app.route('/data/faqs.json')
def serve_faqs():
    """Serve FAQ data for frontend autocomplete"""
    global faqs
    faqs = load_faqs_from_db()
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

@app.route('/admin/login', methods=['POST'])
def admin_login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email, is_admin=True).first()
    if user and check_password_hash(user.password_hash, password):
        session['admin_email'] = email
        session['is_admin'] = True
        return jsonify({'status': 'success'})
    return jsonify({'status': 'fail', 'message': 'Invalid admin credentials'})

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'status': 'success'})

@app.route('/api/ask', methods=['POST'])
def ask():
    data = request.get_json()
    question = data.get('question', '').strip()
    email = session.get('user_email', 'guest')
    answer = None
    is_faq = False
    match_score = 0
    faq_id = None

    print(f"🔍 User question: {question}")

    # Load fresh FAQs from database
    global faqs
    faqs = load_faqs_from_db()

    # STEP 1: Enhanced FAQ Matching
    best_match = find_best_faq_match(question)
    
    if best_match and best_match['score'] >= 70:  # 70% similarity threshold
        answer = best_match['answer']
        # ✅ Fix: Check if answer exists and is not empty
        if answer and answer.strip():
            answer = answer.replace('*', '<br>')
            is_faq = True
            match_score = best_match['score']
            faq_id = best_match.get('id')
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
        Bạn là trợ lý AI thông minh của Swinburne Việt Nam, hỗ trợ tuyển sinh. Sử dụng thông tin FAQ sau để trả lời:

        {faq_context}

        Nếu câu hỏi không liên quan đến Swinburne hoặc thông tin trên, hãy trả lời lịch sự và đề xuất liên hệ bộ phận tuyển sinh. Luôn thân thiện và chuyên nghiệp.

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
        is_faq=is_faq,
        faq_id=faq_id,
        match_score=match_score
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
                'id': faq.get('id'),
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

# === Admin Routes ===
@app.route('/api/admin/faqs', methods=['GET'])
def get_all_faqs():
    if not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    faqs = FAQ.query.order_by(FAQ.priority.desc(), FAQ.created_at.desc()).all()
    return jsonify({
        'faqs': [{
            'id': faq.id,
            'question': faq.question,
            'answer': faq.answer,
            'category': faq.category,
            'keywords': faq.keywords,
            'is_active': faq.is_active,
            'priority': faq.priority,
            'created_at': faq.created_at.strftime('%Y-%m-%d %H:%M:%S')
        } for faq in faqs]
    })

@app.route('/api/admin/faqs', methods=['POST'])
def add_faq():
    if not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    new_faq = FAQ(
        question=data.get('question'),
        answer=data.get('answer'),
        category=data.get('category', 'General'),
        keywords=data.get('keywords', ''),
        priority=data.get('priority', 0)
    )
    
    db.session.add(new_faq)
    db.session.commit()
    
    # Refresh FAQ cache
    global faqs
    faqs = load_faqs_from_db()
    
    return jsonify({'status': 'success', 'id': new_faq.id})

@app.route('/api/admin/faqs/<int:faq_id>', methods=['PUT'])
def update_faq(faq_id):
    if not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    faq = FAQ.query.get_or_404(faq_id)
    
    faq.question = data.get('question', faq.question)
    faq.answer = data.get('answer', faq.answer)
    faq.category = data.get('category', faq.category)
    faq.keywords = data.get('keywords', faq.keywords)
    faq.priority = data.get('priority', faq.priority)
    faq.is_active = data.get('is_active', faq.is_active)
    
    db.session.commit()
    
    # Refresh FAQ cache
    global faqs
    faqs = load_faqs_from_db()
    
    return jsonify({'status': 'success'})

@app.route('/api/admin/faqs/<int:faq_id>', methods=['DELETE'])
def delete_faq(faq_id):
    if not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    faq = FAQ.query.get_or_404(faq_id)
    db.session.delete(faq)
    db.session.commit()
    
    # Refresh FAQ cache
    global faqs
    faqs = load_faqs_from_db()
    
    return jsonify({'status': 'success'})

@app.route('/api/admin/analytics')
def get_analytics():
    if not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Most asked questions
    popular_questions = db.session.query(
        QuestionLog.question, 
        db.func.count(QuestionLog.id).label('count')
    ).group_by(QuestionLog.question).order_by(db.func.count(QuestionLog.id).desc()).limit(10).all()
    
    # FAQ vs AI usage
    faq_usage = QuestionLog.query.filter_by(is_faq=True).count()
    ai_usage = QuestionLog.query.filter_by(is_faq=False).count()
    
    # Unanswered questions (low match scores)
    unanswered = QuestionLog.query.filter(QuestionLog.match_score < 50).order_by(QuestionLog.created_at.desc()).limit(20).all()
    
    return jsonify({
        'popular_questions': [{'question': q[0], 'count': q[1]} for q in popular_questions],
        'usage_stats': {'faq_usage': faq_usage, 'ai_usage': ai_usage},
        'unanswered': [{'question': q.question, 'created_at': q.created_at.strftime('%Y-%m-%d %H:%M:%S')} for q in unanswered]
    })

# === Main ===
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Create admin user if doesn't exist
        admin = User.query.filter_by(email='admin@swinburne.edu.vn').first()
        if not admin:
            admin = User(
                email='admin@swinburne.edu.vn',
                password_hash=generate_password_hash('admin123'),
                name='Admin',
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
            print("✅ Created admin user: admin@swinburne.edu.vn / admin123")
        
        # Migrate JSON FAQs to database
        migrate_json_to_db()
        
        # Load FAQs from database
        faqs = load_faqs_from_db()
    
    print("✅ Flask server running on http://localhost:5000")
    print("✅ Admin panel: http://localhost:5000/admin")
    print(f"✅ Loaded {len(faqs)} FAQs from database")
    app.run(debug=True)