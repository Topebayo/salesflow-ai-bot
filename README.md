# 🚀 WhatsApp AI Sales Agent

An intelligent, AI-powered sales agent that automates WhatsApp conversations using **FastAPI** and **Google Gemini 1.5 Flash**. Built specifically for Nigerian businesses looking to convert leads into clients through smart, persuasive conversational AI.

## ✨ Features

- **AI-Powered Sales Conversations**: Leverages Gemini 1.5 Flash for natural, context-aware responses
- **Nigerian Sales Persona**: Custom-trained prompt for culturally relevant, professional sales conversations
- **WhatsApp Business API Integration**: Full webhook support for receiving and sending messages
- **Conversation Memory**: Maintains context across multiple messages per user
- **Async Architecture**: Built with async/await for optimal performance
- **Clean Error Handling**: Graceful fallbacks and comprehensive logging

## 📁 Project Structure

```
sales_ai_project/
├── main.py              # FastAPI application with webhook endpoints
├── ai_engine.py         # Gemini AI integration with sales prompt
├── requirements.txt     # Python dependencies
├── .env                 # Environment variables (create from template)
├── .gitignore          # Git ignore file
└── README.md           # This file
```

## 🛠️ Setup Instructions

### 1. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

1. Copy the `.env` file and fill in your API keys:

```bash
# Get your Gemini API key from:
# https://makersuite.google.com/app/apikey

# Get your WhatsApp credentials from:
# https://developers.facebook.com/apps/ > Your App > WhatsApp > API Setup

GEMINI_API_KEY=your_actual_gemini_api_key
WHATSAPP_ACCESS_TOKEN=your_whatsapp_access_token
WHATSAPP_VERIFY_TOKEN=your_custom_verify_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
```

### 4. Run the Application

```bash
# Development mode with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Or simply
python main.py
```

### 5. Expose Your Local Server (For Development)

Use ngrok or similar to expose your local server:

```bash
ngrok http 8000
```

Copy the HTTPS URL (e.g., `https://abc123.ngrok.io`)

### 6. Configure Meta Webhook

1. Go to [Meta Developer Console](https://developers.facebook.com/apps/)
2. Select your WhatsApp Business App
3. Navigate to **WhatsApp** > **Configuration**
4. Set Webhook URL: `https://your-ngrok-url/webhook`
5. Set Verify Token: Same as your `WHATSAPP_VERIFY_TOKEN`
6. Subscribe to: `messages` field

## 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check and welcome message |
| `/webhook` | GET | Meta webhook verification |
| `/webhook` | POST | Receives WhatsApp messages |
| `/health` | GET | Application health status |
| `/stats` | GET | Active conversation stats |

## 🤖 AI Sales Persona

The AI agent is configured as **Adaeze**, a professional Nigerian sales closer with:

- Warm, culturally relevant communication style
- Consultative selling methodology
- Built-in objection handling (F.E.A.R. method)
- Always drives toward clear Call-to-Action
- Strategic use of emojis for engagement

## 🔧 Customization

### Modify the Sales Prompt

Edit the `SALES_AGENT_SYSTEM_PROMPT` in `ai_engine.py` to:
- Change the agent's name
- Update your company information
- Modify the sales methodology
- Add specific product/service details

### Add Quick Reply Buttons

```python
# In main.py, modify send_whatsapp_message() to include buttons
payload = {
    "messaging_product": "whatsapp",
    "to": recipient_phone,
    "type": "interactive",
    "interactive": {
        "type": "button",
        "body": {"text": "Your message here"},
        "action": {
            "buttons": [
                {"type": "reply", "reply": {"id": "btn1", "title": "Option 1"}},
                {"type": "reply", "reply": {"id": "btn2", "title": "Option 2"}}
            ]
        }
    }
}
```

## 🚀 Deployment

### Deploy to Railway/Render/Heroku

1. Push your code to GitHub
2. Connect your repository to your hosting platform
3. Set environment variables in the platform dashboard
4. Deploy!

### Production Considerations

- [ ] Use a proper database (Redis/PostgreSQL) for conversation storage
- [ ] Implement rate limiting
- [ ] Add authentication for admin endpoints
- [ ] Set up monitoring and alerting
- [ ] Use production-grade Gemini API quotas

## 📝 Testing

### Test the AI Engine Standalone

```bash
python ai_engine.py
```

### Test Webhook Locally

```bash
# Send a test POST request
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{"object":"whatsapp_business_account","entry":[{"changes":[{"value":{"messages":[{"from":"2348012345678","type":"text","text":{"body":"Hello"}}]}}]}]}'
```

## 🤝 Support

For issues or questions, please open a GitHub issue or contact [your-email@example.com].

## 📄 License

MIT License - Feel free to use and modify for your business needs.

---

Built with ❤️ in Nigeria 🇳🇬
