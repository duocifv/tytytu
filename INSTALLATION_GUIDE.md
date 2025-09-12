# AI Chatbot System - Installation & Testing Guide

## 🚀 Quick Setup

### 1. Install Dependencies
```bash
# Install all required packages
pip install -r requirements.txt
```

### 2. Set Google API Key
```bash
# Option 1: Environment variable (recommended)
export GOOGLE_API_KEY="your-actual-api-key-here"

# Option 2: Modify config/settings.py directly
# Replace "your-google-api-key-here" with your actual key
```

**Get your free Gemini API key at:** https://makersuite.google.com/app/apikey

### 3. Run the System
```bash
# Start the server
python main.py
```

The server will start at: http://localhost:8000

## 🧪 Testing the System

### API Documentation
Visit http://localhost:8000/docs for interactive API testing

### Test Endpoints

#### 1. Health Check
```bash
curl http://localhost:8000/health
```

#### 2. Chat Endpoint
```bash
curl -X POST "http://localhost:8000/chat" \
     -H "Content-Type: application/json" \
     -d '{"question": "Give me health tips for better sleep"}'
```

#### 3. Test Different Tools
```bash
# Blog tool
curl -X POST "http://localhost:8000/chat" \
     -H "Content-Type: application/json" \
     -d '{"question": "Give me blog ideas about AI"}'

# Hydroponics tool
curl -X POST "http://localhost:8000/chat" \
     -H "Content-Type: application/json" \
     -d '{"question": "What pH should I use for hydroponics?"}'

# Fun fact tool
curl -X POST "http://localhost:8000/chat" \
     -H "Content-Type: application/json" \
     -d '{"question": "Tell me a fun fact"}'
```

## 🔧 Troubleshooting

### Common Issues

#### 1. Missing Dependencies
```bash
# If you get import errors, install missing packages:
pip install langchain-community
pip install sentence-transformers
```

#### 2. API Key Issues
- Ensure your Google API key is valid
- Check that the key has Gemini API access enabled
- Verify environment variable is set correctly

#### 3. Port Already in Use
```bash
# If port 8000 is busy, modify config/settings.py:
port: int = 8001  # Change to different port
```

#### 4. ChromaDB Issues
- ChromaDB will create a local database automatically
- If you get permission errors, ensure write access to the project directory

## 📊 Expected Responses

### Successful Chat Response
```json
{
  "answer": "Health tip for sleep: Maintain 7-9 hours of sleep nightly. Create a consistent bedtime routine and avoid screens 1 hour before bed. This helps regulate your circadian rhythm and improves sleep quality.",
  "source": ["Health Tool"],
  "session_id": "uuid-generated-session-id"
}
```

### Health Check Response
```json
{
  "status": "healthy",
  "timestamp": "2025-01-10T14:10:16.123456"
}
```

## 🎯 Testing Checklist

- [ ] Dependencies installed successfully
- [ ] Google API key configured
- [ ] Server starts without errors
- [ ] Health endpoint returns "healthy"
- [ ] Chat endpoint processes questions
- [ ] Different tools are triggered correctly
- [ ] Session memory works across requests
- [ ] RAG retrieval functions for complex queries

## 🔄 Development Mode

For development with auto-reload:
```bash
# The system runs with reload=True by default
python main.py

# Or use uvicorn directly:
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
