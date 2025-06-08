from flask import Flask, request, render_template
import json
import os
import google.generativeai as genai

app = Flask(__name__)

# Load FAQs from JSON file
def load_faqs():
    with open(os.path.join('data', 'faqs.json'), 'r', encoding='utf-8') as f:
        return json.load(f)["faqs"]

faqs = load_faqs()

# Configure Gemini API
genai.configure(api_key="")  # Replace with your Gemini API key
model = genai.GenerativeModel('gemini-2.0-flash-exp')

@app.route('/', methods=['GET', 'POST'])
def index():
    answer = None
    question = ''
    if request.method == 'POST':
        question = request.form['question'].lower()
        for faq in faqs:
            if isinstance(faq, dict):
                faq_question = faq.get('question', '')
                if isinstance(faq_question, str) and question in faq_question.lower():
                    answer = faq.get('answer', 'No answer available.').replace('*', '<br>')
                    break
        if not answer:
            # Fallback to Gemini API
            prompt = (
                "You are a helpful assistant for Swinburne Counsulting Service. "
                "If you don't know the answer, say you don't know. "
                f"User question: {question}"
            )
            response = model.generate_content(prompt)
            answer = response.text.replace('*', '<br>')
    return render_template('test.html', answer=answer, question=question)

if __name__ == '__main__':
    app.run(debug=True)