from flask import Flask, render_template, request, jsonify
import os, time, logging
from flask_cors import CORS
from functools import wraps
from datetime import datetime, timedelta
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__, template_folder='backend/templates')
CORS(app)

# ===== ENVIRONMENT CONFIGURATION =====
# API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash-latest")

# Model Parameters
MODEL_TEMPERATURE = float(os.getenv("MODEL_TEMPERATURE", "0.7"))
MODEL_TOP_K = int(os.getenv("MODEL_TOP_K", "40"))
MODEL_TOP_P = float(os.getenv("MODEL_TOP_P", "0.95"))
MODEL_MAX_OUTPUT_TOKENS = int(os.getenv("MODEL_MAX_OUTPUT_TOKENS", "1024"))

# Persona Configuration
AI_NAME = os.getenv("AI_NAME", "Yash Sinha")
AI_ROLE = os.getenv("AI_ROLE", "final-year B.Tech AI/ML student")
AI_STYLE = os.getenv("AI_STYLE", "friendly, confident, and clear")

# Security & Rate Limiting
MAX_INPUT_LENGTH = int(os.getenv("MAX_INPUT_LENGTH", "500"))
MAX_REQUESTS_PER_MINUTE = int(os.getenv("MAX_REQUESTS_PER_MINUTE", "20"))
RETRY_ATTEMPTS = int(os.getenv("RETRY_ATTEMPTS", "3"))
RETRY_DELAY = int(os.getenv("RETRY_DELAY", "1"))

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_API_REQUESTS = os.getenv("LOG_API_REQUESTS", "false").lower() == "true"

# Configure logging
logging.basicConfig(level=getattr(logging, LOG_LEVEL))
logger = logging.getLogger(__name__)

# Validate required configuration
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is required")

# Configure Google AI SDK
genai.configure(api_key=GEMINI_API_KEY)

# Rate limiting storage (in production, use Redis or database)
request_history = {}

def rate_limit(f):
    """Rate limiting decorator"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        current_time = datetime.now()
        
        # Clean old requests
        if client_ip in request_history:
            request_history[client_ip] = [
                req_time for req_time in request_history[client_ip]
                if current_time - req_time < timedelta(minutes=1)
            ]
        else:
            request_history[client_ip] = []
        
        # Check rate limit
        if len(request_history[client_ip]) >= MAX_REQUESTS_PER_MINUTE:
            return jsonify({"error": "Rate limit exceeded. Please try again later."}), 429
        
        request_history[client_ip].append(current_time)
        return f(*args, **kwargs)
    return decorated_function

def call_gemini_api(question, retry_count=0):
    """Call Gemini API using Google AI SDK"""
    try:
        # Configure the model with environment settings
        generation_config = genai.types.GenerationConfig(
            temperature=MODEL_TEMPERATURE,
            top_k=MODEL_TOP_K,
            top_p=MODEL_TOP_P,
            max_output_tokens=MODEL_MAX_OUTPUT_TOKENS,
        )
        
        # Configure safety settings - more permissive for chat
        safety_settings = [
            {
                "category": genai.types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                "threshold": genai.types.HarmBlockThreshold.BLOCK_ONLY_HIGH
            },
            {
                "category": genai.types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                "threshold": genai.types.HarmBlockThreshold.BLOCK_ONLY_HIGH
            },
            {
                "category": genai.types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                "threshold": genai.types.HarmBlockThreshold.BLOCK_ONLY_HIGH
            },
            {
                "category": genai.types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                "threshold": genai.types.HarmBlockThreshold.BLOCK_ONLY_HIGH
            }
        ]
        
        # Create model instance
        model = genai.GenerativeModel(
            model_name=GEMINI_MODEL,
            generation_config=generation_config,
            safety_settings=safety_settings
        )
        
        # Build the prompt
        prompt = f"""You are {AI_NAME}, a {AI_ROLE}.
Respond like {AI_NAME} — {AI_STYLE}.
Keep responses concise and engaging.

Question: {question}"""
        
        # Log API request if enabled
        if LOG_API_REQUESTS:
            logger.debug(f"Calling model: {GEMINI_MODEL}")
            logger.debug(f"Prompt: {prompt}")
        
        # Generate response
        response = model.generate_content(prompt)
        
        # Check if response was blocked
        if not response.candidates:
            logger.warning("Response was blocked - no candidates returned")
            return "I'm sorry, but I can't provide a response to that question due to safety guidelines. Please try rephrasing your question."
        
        candidate = response.candidates[0]
        
        # Check finish reason using the actual enum values
        if candidate.finish_reason == candidate.FinishReason.SAFETY:
            logger.warning(f"Response blocked by safety filter. Safety ratings: {candidate.safety_ratings}")
            return "I apologize, but my response was blocked by safety filters. Could you please rephrase your question in a different way?"
        
        elif candidate.finish_reason == candidate.FinishReason.MAX_TOKENS:
            logger.warning("Response truncated due to max tokens limit")
            # Still return the partial response if available
            if candidate.content and candidate.content.parts:
                return candidate.content.parts[0].text + " [Response truncated - please ask for continuation]"
            else:
                return "My response was too long and got cut off. Please ask me to continue or rephrase your question."
        
        elif candidate.finish_reason not in [candidate.FinishReason.STOP, candidate.FinishReason.MAX_TOKENS]:
            logger.warning(f"Unexpected finish reason: {candidate.finish_reason}")
            return "I encountered an unexpected issue generating a response. Please try again."
        
        # Extract text safely
        if candidate.content and candidate.content.parts:
            response_text = candidate.content.parts[0].text
            
            if LOG_API_REQUESTS:
                logger.debug(f"Response: {response_text}")
            
            return response_text
        else:
            logger.warning("No content in response parts")
            return "I'm sorry, I couldn't generate a proper response. Please try again."
        
    except Exception as e:
        if retry_count < RETRY_ATTEMPTS - 1:
            time.sleep(RETRY_DELAY * (retry_count + 1))
            return call_gemini_api(question, retry_count + 1)
        else:
            error_msg = str(e).lower()
            if "api key" in error_msg or "authentication" in error_msg:
                logger.error(f"Gemini API authentication error: {e}")
                return "❌ Authentication Error: Please check your API key configuration."
            elif "quota" in error_msg or "limit" in error_msg:
                logger.error(f"Gemini API quota exceeded: {e}")
                return "❌ Quota Exceeded: API usage limit reached. Please try again later."
            elif "model not found" in error_msg or "not found" in error_msg:
                logger.error(f"Gemini model not found: {GEMINI_MODEL}, Error: {e}")
                return f"❌ Model Error: The model '{GEMINI_MODEL}' is not available. Please check your configuration."
            elif "response.text" in str(e) and ("finish_reason" in str(e) or "valid `Part`" in str(e)):
                logger.error(f"Response blocked by safety filters: {e}")
                return "I apologize, but my response was filtered for safety reasons. Please try rephrasing your question in a more neutral way."
            else:
                logger.error(f"Gemini API error after {RETRY_ATTEMPTS} attempts: {e}")
                return "Sorry, I'm having trouble connecting to my AI brain right now. Please try again in a moment!"

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
@rate_limit
def ask():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON data"}), 400
            
        question = data.get("question", "").strip()

        # Input validation
        if not question:
            return jsonify({"error": "Please say or type something!"})
        
        if len(question) > MAX_INPUT_LENGTH:
            return jsonify({"error": f"Question too long. Please keep it under {MAX_INPUT_LENGTH} characters."})

        # Sanitize input (basic)
        question = question.replace('<', '&lt;').replace('>', '&gt;')

        # Call AI API
        reply = call_gemini_api(question)
        
        return jsonify({
            "reply": reply,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in /ask endpoint: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/health")
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "model": GEMINI_MODEL,
        "ai_name": AI_NAME,
        "sdk": "google-generativeai"
    })

@app.route("/config")
def config():
    """Configuration endpoint (for debugging)"""
    return jsonify({
        "model": GEMINI_MODEL,
        "ai_name": AI_NAME,
        "ai_role": AI_ROLE,
        "temperature": MODEL_TEMPERATURE,
        "max_tokens": MODEL_MAX_OUTPUT_TOKENS,
        "rate_limit": MAX_REQUESTS_PER_MINUTE,
        "environment": os.getenv("ENVIRONMENT", "development"),
        "sdk": "google-generativeai"
    })

if __name__ == "__main__":
    # Server configuration from environment
    debug_mode = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    port = int(os.getenv("PORT", "5000"))
    host = os.getenv("HOST", "0.0.0.0")
    
    # Print configuration summary
    print(f"🤖 AI: {AI_NAME} ({AI_ROLE})")
    print(f"🧠 Model: {GEMINI_MODEL}")
    print(f"🌡️ Temperature: {MODEL_TEMPERATURE}")
    print(f"📊 Max Tokens: {MODEL_MAX_OUTPUT_TOKENS}")
    print(f"🛡️ Rate Limit: {MAX_REQUESTS_PER_MINUTE}/min")
    print(f"⚡ SDK: google-generativeai")
    print(f"🚀 Starting server on {host}:{port}")
    
    app.run(
        host=host, 
        port=port, 
        debug=debug_mode
    )