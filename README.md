# 🎙️ Yash's VoiceBot 100X

A sophisticated AI voice chatbot powered by Google Gemini Pro, featuring real-time conversation, speech recognition, and text-to-speech capabilities.

## ✨ Features

- **🎤 Voice Input**: Web Speech Recognition for hands-free interaction
- **🔊 Voice Output**: Text-to-speech with natural Indian English
- **💬 Conversation History**: Complete chat history with timestamps
- **⚡ Real-time Feedback**: Typing indicators and loading states
- **🛡️ Security**: Rate limiting, input validation, and error handling
- **📱 Responsive Design**: Works on desktop and mobile devices
- **🚀 Production Ready**: Environment variables, retry logic, and health checks

## 🏗️ Architecture

### Backend (Flask)
- **Framework**: Flask with CORS support
- **AI Integration**: Google Gemini Pro API
- **Security**: Rate limiting (20 req/min), input sanitization
- **Error Handling**: Retry logic with exponential backoff
- **Production**: Environment-based configuration

### Frontend (Vanilla JS)
- **Speech Recognition**: Web Speech API
- **Text-to-Speech**: Speech Synthesis API  
- **UI**: Modern responsive design with conversation history
- **Error Handling**: Graceful degradation and user feedback

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Google Gemini API key ([Get one here](https://ai.google.dev/))

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd "voice bot 100X"
   ```

2. **Install dependencies**
   ```bash
   pip install -r backend/requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   # Windows PowerShell
   $env:GEMINI_API_KEY="your_api_key_here"
   
   # Linux/Mac
   export GEMINI_API_KEY="your_api_key_here"
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Open your browser**
   Navigate to `http://localhost:5000`

## 🛠️ Development

### Environment Variables
```bash
GEMINI_API_KEY=your_gemini_api_key    # Required
FLASK_DEBUG=true                      # Optional: Enable debug mode
PORT=5000                             # Optional: Custom port
```

### Project Structure
```
voice bot 100X/
├── app.py                    # Main Flask application
├── backend/
│   ├── requirements.txt      # Python dependencies
│   └── templates/
│       └── index.html        # Frontend interface
└── README.md                 # This file
```

## 🚀 Production Deployment

### Using Gunicorn (Recommended)
```bash
# Install gunicorn (already in requirements.txt)
pip install gunicorn

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Environment Setup for Production
```bash
export GEMINI_API_KEY="your_production_api_key"
export FLASK_DEBUG=false
export PORT=5000
```

### Health Check
The app includes a health check endpoint:
```bash
curl http://localhost:5000/health
```

## 🔧 Configuration

### Rate Limiting
- **Default**: 20 requests per minute per IP
- **Configurable**: Modify `MAX_REQUESTS_PER_MINUTE` in `app.py`

### Input Validation
- **Max Length**: 500 characters
- **Sanitization**: HTML entity encoding
- **Required**: Non-empty questions

### API Timeouts
- **Request Timeout**: 10 seconds
- **Retry Attempts**: 3 times
- **Retry Delay**: Exponential backoff (1s, 2s, 3s)

## 🎯 API Endpoints

### `GET /`
Serves the main chat interface

### `POST /ask`
Process chat questions
```json
{
  "question": "Your question here"
}
```

**Response:**
```json
{
  "reply": "AI response",
  "timestamp": "2024-01-01T12:00:00"
}
```

### `GET /health`
Health check endpoint
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00",
  "version": "1.0.0"
}
```

## 🐛 Troubleshooting

### Common Issues

1. **"GEMINI_API_KEY environment variable is required"**
   - Set the API key as an environment variable
   - Ensure no spaces around the `=` sign

2. **Speech recognition not working**
   - Use HTTPS or localhost (required for Web Speech API)
   - Check browser compatibility (Chrome recommended)

3. **Rate limit exceeded**
   - Wait 1 minute or adjust `MAX_REQUESTS_PER_MINUTE`

4. **API timeout errors**
   - Check internet connection
   - Verify API key is valid
   - Check Gemini API service status

## 🔒 Security Features

- **Environment Variables**: No hardcoded API keys
- **Rate Limiting**: Prevents API abuse
- **Input Validation**: Length and content sanitization  
- **Error Handling**: No sensitive data in error messages
- **CORS**: Configured for web security

## 📈 Performance

- **Response Time**: < 2s average (depends on Gemini API)
- **Concurrent Users**: Scales with gunicorn workers
- **Memory Usage**: ~50MB per worker
- **Rate Limit**: 20 requests/minute/IP

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📜 License

This project is licensed under the MIT License.

## 👨‍💻 About

Created by **Yash Sinha** - Final-year B.Tech AI/ML student passionate about building intelligent conversational systems.

---

**Happy Chatting!** 🚀🤖