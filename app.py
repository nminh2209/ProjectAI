from flask import Flask, request, render_template, jsonify, session
import json
import os
import google.generativeai as genai

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Required for user sessions

# Load FAQs from JSON file
def load_faqs():
    with open(os.path.join('data', 'faqs.json'), 'r', encoding='utf-8') as f:
        return json.load(f)["faqs"]

faqs = load_faqs()

# Configure Gemini API
genai.configure(api_key="AIzaSyAzsMfSo_LqpnwI6eBcxgW1ZbnCGcXfnDA")
model = genai.GenerativeModel('gemini-2.0-flash-exp')

@app.route('/')
def index():
    return render_template('test.html')

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    if email:
        session['user_email'] = email
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': 'Email required'}), 400

@app.route('/api/ask', methods=['POST'])
def ask():
    data = request.get_json()
    question = data.get('question', '').lower()
    answer = None

    for faq in faqs:
        if isinstance(faq, dict):
            faq_question = faq.get('question', '')
            if isinstance(faq_question, str) and question in faq_question.lower():
                answer = faq.get('answer', 'No answer available.').replace('*', '<br>')
                break

    if not answer:
        prompt = (
            "You are a helpful assistant for Swinburne VietNam Admission Service. "
            "If you don't know the answer, say you will contact to the HQ team (in Vietnamese) "
            f"User question: {question}"
        )
        response = model.generate_content(prompt)
        answer = response.text.replace('*', '<br>')

        # Save unanswered question
        email = session.get('user_email', 'guest')
        with open('data/unanswered.json', 'a', encoding='utf-8') as f:
            f.write(json.dumps({"email": email, "question": question}) + '\n')

    return jsonify({'answer': answer})

@app.route('/api/save_unanswered', methods=['POST'])
def save_unanswered():
    data = request.get_json()
    question = data.get('question')
    email = session.get('user_email', 'anonymous')
    with open('data/unanswered.json', 'a', encoding='utf-8') as f:
        f.write(json.dumps({'email': email, 'question': question}) + '\n')
    return jsonify({'status': 'saved'})

if __name__ == '__main__':
    print("✅ Flask app starting...")
    app.run(debug=True)
