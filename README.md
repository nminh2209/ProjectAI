# Swinburne University Counseling Chatbot System

## Overview

This is a comprehensive chatbot system developed for Swinburne University's counseling services. The system integrates Google's Gemini AI with a structured FAQ database to provide intelligent responses to student inquiries in both Vietnamese and English. It features user authentication, responsive design, and admin support capabilities.

## System Architecture

### Backend Components

- **Flask Web Framework**: Serves as the main application server
- **Google Gemini API**: Provides AI-powered responses using `gemini-2.0-flash-exp` model
- **JSON Database**: Stores structured FAQ data for quick retrieval
- **Session Management**: Handles user authentication and state

### Frontend Components

- **Responsive Web Interface**: Bootstrap-based responsive design
- **Floating Chatbot Widget**: Integrated into Swinburne website
- **Authentication Modals**: Login and registration interfaces
- **Admin Support Panel**: Direct contact and feedback system

## Features

### Core Functionality

- **FAQ Matching**: Intelligent fuzzy matching for common questions
- **AI Fallback**: Gemini AI responses when FAQ matches aren't found
- **Bilingual Support**: Vietnamese and English language support
- **User Authentication**: Registration and login system
- **Session Persistence**: Maintains conversation state

### User Interface

- **Floating Widget**: Non-intrusive chatbot widget
- **Suggestion Engine**: Quick-access buttons for common queries
- **Feedback System**: User rating and feedback collection
- **Admin Contact**: Direct hotline and support request forms
- **Responsive Design**: Mobile and desktop optimization

### Administrative Features

- **Contact Management**: Admin notification system
- **User Registration**: Account creation and management
- **Session Tracking**: User state persistence
- **Support Requests**: Integrated help desk functionality

## Installation Guide

### Prerequisites

```bash
Python 3.8+
pip package manager
Google Cloud API credentials
```

### Setup Instructions

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd GeminiAPItest
   ```

2. **Install Dependencies**
   ```bash
   pip install flask google-generativeai
   ```

3. **Configure Environment**
   - Set up Google Gemini API key
   - Configure API credentials in app.py

4. **Run the Application**
   ```bash
   python app.py
   ```

5. **Access the System**
   - Main interface: `http://localhost:5000`
   - Integrated widget: `http://localhost:5000/test`

## API Documentation

### Endpoints

#### Chat Endpoint
```http
POST /api/ask
Content-Type: application/json

{
    "question": "User question text"
}

Response:
{
    "response": "AI/FAQ response text"
}
```

#### Authentication Endpoints
```http
POST /api/login
Content-Type: application/json

{
    "username": "user@example.com",
    "password": "userpassword"
}

POST /api/register
Content-Type: application/json

{
    "username": "user@example.com",
    "password": "userpassword",
    "fullName": "User Full Name"
}
```

#### Static Routes
```http
GET /              # Main chatbot interface
GET /test          # Integrated Swinburne website
GET /teas          # Additional interface
```

## File Structure

```
GeminiAPItest/
├── app.py                 # Main Flask application
├── README.md             # This documentation
├── data/
│   └── faqs.json         # FAQ database
├── static/
│   └── chatbot.css       # Styling and animations
├── templates/
│   ├── index.html        # Main chatbot interface
│   ├── test.html         # Integrated website
│   └── teas.html         # Alternative interface
├── instance/
│   └── chatbot.db        # SQLite database (if used)
└── __pycache__/          # Python cache files
```

## Configuration

### FAQ Database Structure

The `data/faqs.json` file contains structured Q&A pairs:

```json
{
    "faqs": [
        {
            "question": "Question text",
            "answer": "Detailed answer",
            "category": "admissions|portal|programs",
            "keywords": ["key", "words"]
        }
    ]
}
```

### Gemini AI Configuration

The system uses Google's `gemini-2.0-flash-exp` model with context awareness for Swinburne University counseling services.

## User Guide

### For Students

1. **Access the Chatbot**: Click the floating chat icon on any Swinburne page
2. **Ask Questions**: Type questions about admissions, programs, or university services
3. **Use Suggestions**: Click quick-access buttons for common queries
4. **Register Account**: Create an account for personalized experience
5. **Provide Feedback**: Rate responses and provide improvement suggestions

### For Administrators

1. **Monitor Conversations**: Track user interactions and common queries
2. **Update FAQ Database**: Modify `data/faqs.json` for new information
3. **Manage Support Requests**: Handle direct contact form submissions
4. **System Maintenance**: Regular updates and performance monitoring

## Technical Specifications

### Performance

- **Response Time**: < 2 seconds for FAQ matches
- **AI Fallback**: 3-5 seconds for Gemini responses
- **Concurrent Users**: Supports multiple simultaneous sessions
- **Database**: Efficient JSON-based FAQ retrieval

### Security

- **Session Management**: Secure user authentication
- **Input Validation**: Sanitized user inputs
- **API Security**: Protected endpoint access
- **Data Privacy**: Compliant with university standards

### Browser Compatibility

- **Chrome**: Full support (recommended)
- **Firefox**: Full support
- **Safari**: Full support
- **Edge**: Full support
- **Mobile**: Responsive design for all devices

## Deployment

### Production Deployment

1. **Server Requirements**
   - Python 3.8+ runtime
   - 1GB RAM minimum
   - SSL certificate for HTTPS

2. **Environment Variables**
   ```bash
   FLASK_ENV=production
   GEMINI_API_KEY=your_api_key
   SECRET_KEY=your_secret_key
   ```

3. **Web Server Configuration**
   - Use Gunicorn or uWSGI for production
   - Configure reverse proxy (Nginx/Apache)
   - Enable SSL/TLS encryption

### Monitoring and Maintenance

- **Log Management**: Configure application logging
- **Performance Monitoring**: Track response times and errors
- **Database Backups**: Regular FAQ database backups
- **Security Updates**: Keep dependencies updated

## Troubleshooting

### Common Issues

1. **API Key Errors**: Verify Gemini API credentials
2. **Template Errors**: Check Jinja2 syntax in HTML files
3. **CSS Loading Issues**: Verify static file paths
4. **Database Errors**: Check FAQ JSON file format

### Debug Mode

Enable Flask debug mode for development:
```python
app.run(debug=True, host='0.0.0.0', port=5000)
```

## Contributing

### Development Guidelines

1. **Code Style**: Follow PEP 8 for Python code
2. **Documentation**: Update README for new features
3. **Testing**: Test all changes thoroughly
4. **Version Control**: Use meaningful commit messages

### Adding New Features

1. **FAQ Updates**: Modify `data/faqs.json`
2. **UI Changes**: Update templates and CSS
3. **API Endpoints**: Extend Flask routes in `app.py`
4. **Documentation**: Update this README

## License

This project is developed for Swinburne University of Technology. All rights reserved.

## Support

For technical support or questions:
- **Email**: Contact university IT support
- **Documentation**: Refer to this README
- **Issues**: Report bugs through appropriate channels

## Version History

- **v1.0**: Initial release with basic FAQ functionality
- **v1.1**: Added Gemini AI integration
- **v1.2**: Implemented user authentication
- **v1.3**: Added responsive design and widget integration
- **v1.4**: Enhanced admin features and Vietnamese support

---

*Last Updated: December 2024*
*Developed for Swinburne University Counseling Services*