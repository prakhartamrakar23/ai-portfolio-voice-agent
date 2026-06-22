# AI-Powered Portfolio with RAG Voice Assistant

A modern, interactive portfolio website featuring an AI-powered voice assistant that answers questions about your background, skills, projects, and experience using RAG (Retrieval Augmented Generation).

## 🎯 Features

- **🎤 Voice Interaction**: Speech-to-text input using Groq Whisper API
- **💬 Text Chat**: Traditional text-based chat interface
- **🔊 Voice Output**: Browser-based text-to-speech responses
- **🧠 RAG-Powered Responses**: Intelligent answers based on your knowledge base
- **📄 PDF Upload & Processing**: Upload resumes, project docs, or any PDF files
- **📚 Dynamic Knowledge Base**: Automatic vector embedding and retrieval
- **🎨 Modern UI**: Responsive design with animated components
- **🆓 100% Free Deployment**: No cost for typical portfolio traffic

## 🏗️ Architecture

```
Portfolio/
├── frontend/                    # Static HTML/CSS/JS frontend
│   ├── index.html              # Main portfolio page
│   ├── upload.html             # PDF upload interface
│   ├── main.js                 # Frontend logic & AI agent
│   ├── upload-script.js        # PDF upload functionality
│   ├── style.css               # Main styling
│   └── public/
│       └── images.jpg          # Profile image
│
├── backend/                     # FastAPI backend
│   ├── config/                 # Configuration management
│   │   ├── __init__.py
│   │   └── config.py           # Centralized config (API keys, settings)
│   ├── main.py                 # FastAPI app & endpoints
│   ├── rag.py                  # RAG retrieval logic
│   ├── vector_store.py         # ChromaDB vector store
│   ├── pdf_ingestion.py        # PDF processing pipeline
│   ├── requirements.txt        # Python dependencies
│   ├── .env                    # Environment variables (not in git)
│   ├── .env.example            # Environment template
│   ├── chroma_db/              # Vector database (auto-created)
│   └── uploaded_pdfs/          # Uploaded PDF storage
│
└── README.md                    # This file
```

## 🛠️ Tech Stack

### Frontend
- **HTML/CSS/JavaScript**: Pure vanilla JS for lightweight performance
- **Browser Speech Synthesis**: Free client-side text-to-speech
- **Responsive Design**: Works on desktop, tablet, and mobile

### Backend
- **FastAPI**: Modern Python web framework
- **Groq API**: 
  - Llama 3.3 70B for LLM responses (free tier)
  - Whisper Large v3 for speech-to-text (free tier)
- **ChromaDB**: Embedded vector database (file-based, no server needed)
- **Sentence Transformers**: Local embeddings generation
- **Python-dotenv**: Environment variable management

### Deployment
- **Frontend**: Vercel, Netlify, or GitHub Pages (free static hosting)
- **Backend**: Render free tier (sleeps after 15min inactivity)

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Node.js (optional, for Vercel deployment)
- Groq API key (free at [console.groq.com](https://console.groq.com))

### 1. Clone & Setup Backend

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
```

### 2. Configure Your Settings

Edit `backend/.env` with your preferences:

```env
# Required: Get from console.groq.com
GROQ_API_KEY=your_groq_api_key_here

# Optional: Customize LLM behavior
LLM_MODEL=llama-3.3-70b-versatile
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=1024

# Optional: RAG settings
RETRIEVAL_TOP_K=5
CHUNK_SIZE=500
CHUNK_OVERLAP=50

# Optional: CORS for production
CORS_ORIGINS=http://localhost:8080,https://yourportfolio.com
```

### 3. Add Your Content

**Option A: Upload PDFs (Recommended)**

1. Start the backend server:
   ```bash
   cd backend
   uvicorn main:app --reload --port 8000
   ```

2. Open the upload interface:
   ```
   http://localhost:8000/upload.html
   ```

3. Upload your resume, project docs, or any PDF files
4. The system will automatically process and embed them

**Option B: Manual Markdown (Legacy)**

Edit files in `backend/knowledge_base/`:
- `about_me.md` - Bio, education, contact
- `skills.md` - Technical skills
- `projects.md` - Portfolio projects
- `experience.md` - Work experience

Then run:
```bash
python build_kb.py
```

### 4. Test Locally

**Terminal 1 - Backend:**
```bash
cd backend
uvicorn main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
python -m http.server 8080
```

Visit: **http://localhost:8080**

Test the AI assistant by:
- Clicking the microphone button (bottom right)
- Asking questions about your background, skills, or projects

## 📝 Configuration Options

All settings are managed in `backend/config/config.py` and can be overridden via environment variables in `.env`:

| Setting | Default | Description |
|---------|---------|-------------|
| `GROQ_API_KEY` | Required | Your Groq API key |
| `LLM_MODEL` | `llama-3.3-70b-versatile` | Language model to use |
| `LLM_TEMPERATURE` | `0.7` | Response creativity (0-1) |
| `LLM_MAX_TOKENS` | `1024` | Maximum response length |
| `STT_MODEL` | `whisper-large-v3` | Speech-to-text model |
| `RETRIEVAL_TOP_K` | `5` | Number of context chunks to retrieve |
| `CHUNK_SIZE` | `500` | Text chunk size for embeddings |
| `CHUNK_OVERLAP` | `50` | Overlap between chunks |
| `UPLOAD_FOLDER` | `./uploaded_pdfs` | PDF storage location |
| `MAX_FILE_SIZE` | `10485760` | Max upload size (10MB) |
| `CORS_ORIGINS` | `http://localhost:8080` | Allowed frontend URLs |

## 🌐 Deployment

### Deploy Backend to Render

1. Push your code to GitHub
2. Go to [render.com](https://render.com) → New → Web Service
3. Connect your repository
4. Configure:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables:
   - `GROQ_API_KEY=your_key_here`
   - `CORS_ORIGINS=https://yourfrontend.vercel.app`
6. Deploy and copy your URL (e.g., `https://yourapp.onrender.com`)

### Deploy Frontend

**Option A: Vercel (Recommended)**
```bash
npm i -g vercel
cd frontend
# Update BACKEND_URL in main.js to your Render URL
vercel --prod
```

**Option B: Netlify**
1. Update `BACKEND_URL` in `frontend/main.js` to your Render URL
2. Drag `frontend/` folder to [netlify.com](https://netlify.com)

**Option C: GitHub Pages**
1. Update `BACKEND_URL` in `frontend/main.js`
2. Push to GitHub
3. Enable Pages in repository settings

## 📊 API Endpoints

### Chat Endpoints
- `POST /chat` - Send message to AI assistant
- `POST /transcribe` - Convert audio to text

### Knowledge Base Management
- `POST /upload-pdf` - Upload single PDF
- `POST /upload-multiple-pdfs` - Upload multiple PDFs
- `GET /list-pdfs` - List all uploaded PDFs
- `DELETE /delete-pdf/{filename}` - Remove specific PDF
- `POST /rebuild-kb` - Rebuild entire knowledge base
- `POST /clear-kb` - Clear all knowledge base data
- `GET /kb-stats` - Get knowledge base statistics

### Utility
- `GET /health` - Health check
- `GET /debug-collection` - Debug vector database

## 💰 Free Tier Limits

- **Groq API**: 
  - 2,000 audio transcriptions/day
  - 1,000 LLM requests/day
  - More than enough for portfolio traffic
- **Render**: Sleeps after 15min inactivity (30-60s cold start)
- **Vercel/Netlify**: Unlimited static hosting

**Estimated cost for typical portfolio**: **$0/month**

## 🎨 Customization

### Update AI Assistant Personality

Edit `backend/config/config.py` → `SYSTEM_PROMPT`:

```python
SYSTEM_PROMPT = """You are [YOUR NAME]'s AI portfolio assistant...
[Customize personality and tone here]
"""
```

### Modify Frontend Styling

Edit `frontend/style.css` - Change colors, fonts, animations

### Adjust Welcome Message

Edit `frontend/main.js` → Line ~481:

```javascript
addAgentMessage("Your custom welcome message here", 'assistant');
```

### Change Profile Image

Replace `frontend/public/images.jpg` with your image

## 🐛 Troubleshooting

### "No information in knowledge base"
- Upload PDFs via `/upload.html`
- Check backend logs for processing errors
- Verify `chroma_db/` folder was created

### CORS errors
- Update `CORS_ORIGINS` in `.env` to include your frontend URL
- Restart backend after changes

### Backend cold start (Render)
- First request after 15min takes 30-60s
- Consider using an uptime monitor (e.g., UptimeRobot)

### Audio not transcribing
- Check microphone permissions in browser
- Verify GROQ_API_KEY is set correctly
- Check browser console for errors

## 📚 Documentation

- [PDF Ingestion Guide](./PDF_INGESTION_GUIDE.md)
- [Deployment Guide](./DEPLOYMENT_GUIDE.md)
- [Quick Start PDF](./QUICK_START_PDF.md)

## 🤝 Contributing

This is a personal portfolio template. Feel free to fork and customize for your own use!

## 📄 License

MIT License - Feel free to use this for your own portfolio

## 🙋 Support

- Check the documentation files for detailed guides
- Review API endpoints at `http://localhost:8000/docs` (when backend is running)
- Inspect browser console for frontend errors
- Check backend terminal for server-side logs

---

**Built with ❤️ using Python, FastAPI, and Groq AI**
