"""
Configuration management for the Portfolio RAG backend.
Reads settings from environment variables with fallbacks.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


class Config:
    """Application configuration"""
    
    # API Keys
    GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')
    
    # LLM Settings
    LLM_MODEL = os.getenv('LLM_MODEL', 'llama-3.3-70b-versatile')
    LLM_TEMPERATURE = float(os.getenv('LLM_TEMPERATURE', '0.7'))
    LLM_MAX_TOKENS = int(os.getenv('LLM_MAX_TOKENS', '1024'))
    
    # STT Settings
    STT_MODEL = os.getenv('STT_MODEL', 'whisper-large-v3')
    
    # Vector DB Settings
    CHROMA_DB_PATH = os.getenv('CHROMA_DB_PATH', './chroma_db')
    COLLECTION_NAME = os.getenv('COLLECTION_NAME', 'portfolio_kb')
    
    # RAG Settings
    RETRIEVAL_TOP_K = int(os.getenv('RETRIEVAL_TOP_K', '5'))
    CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', '500'))
    CHUNK_OVERLAP = int(os.getenv('CHUNK_OVERLAP', '50'))
    
    # File Upload Settings
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', './uploaded_pdfs')
    MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', '10485760'))  # 10MB default
    ALLOWED_EXTENSIONS = {'pdf', 'txt', 'md'}
    
    # CORS Settings
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:8080,http://127.0.0.1:8080').split(',')
    
    # System Prompt
    SYSTEM_PROMPT = """You are Prakhar's AI portfolio assistant. You have deep knowledge about his:
- Background, education, and professional experience
- Technical skills in AI/ML, Generative AI, LangChain, Azure AI, RAG systems, and MCP
- Projects including CSA RFQ System, InfoBeans AI Homepage, and ASHRAE Document Processing
- Work at InfoBeans Technologies as a Trainee Software Engineer
- OFF-TOPIC RULE: If the user asks about something unrelated to Prakhar (like recipes, general trivia, or weather), give an extremely short, polite refusal (1-2 sentence max). Do NOT list his skills. Just genetly guide them back to portfolio.

Be conversational, professional, and enthusiastic. Provide specific details from the knowledge base.
If asked about something not in your knowledge, politely say you don't have that information.
Keep responses concise but informative."""

    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is required. Please set it in the .env file.")
        return True


# Create config instance
config = Config()
