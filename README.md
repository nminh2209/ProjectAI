# Swinburne Consulting Chatbot

This is a Flask-based web chatbot for Swinburne Consulting Service. It answers questions using a local FAQ database and Google Gemini AI as a fallback.

## Features

- Answers common questions from a local FAQ JSON file.
- Uses Google Gemini AI for questions not found in the FAQ.
- Simple web interface styled with Bootstrap.

## Project Structure

```
app.py
data/
    faqs.json
static/
    chatbot.css
templates/
    index.html
    test.html
```

## Requirements

- Python 3.8+
- Flask
- google-generativeai

## Installation

1. Clone the repository.
2. Install dependencies:
    ```sh
    pip install flask google-generativeai
    ```
3. Add your Gemini API key in `app.py`:
    ```python
    genai.configure(api_key="YOUR_GEMINI_API_KEY")
    ```

## Running the App

```sh
python app.py
```

Visit [http://localhost:5000](http://localhost:5000) in your browser.

## FAQ Data

Edit `data/faqs.json` to add or update FAQs.

## License

MIT License