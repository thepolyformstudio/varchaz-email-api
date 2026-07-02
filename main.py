import os
import smtplib
from email.message import EmailMessage
from fastapi import FastAPI, HTTPException, Security
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# App Configuration
API_KEY = os.getenv("API_KEY", "change-me-in-production")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", SMTP_USERNAME)

# Setup App & CORS
app = FastAPI(title="Varchaz Email Microservice")

# Allow the frontend to access this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "https://varchaz-app.web.app",
        "https://varchaz-app.firebaseapp.com"
    ],
    allow_credentials=True,
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["*"],
)

# API Key Dependency
api_key_header = APIKeyHeader(name="x-api-key", auto_error=True)

def get_api_key(api_key: str = Security(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return api_key

# Request Model
class EmailRequest(BaseModel):
    to: str
    subject: str
    html: str
    text: str = ""

@app.get("/")
def health_check():
    return {"status": "ok", "message": "Varchaz Email Microservice is running."}

@app.post("/send")
def send_email(request: EmailRequest, api_key: str = Security(get_api_key)):
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        raise HTTPException(status_code=500, detail="SMTP credentials not configured on server.")

    try:
        # Construct the email
        msg = EmailMessage()
        msg["Subject"] = request.subject
        msg["From"] = SENDER_EMAIL
        msg["To"] = request.to
        
        # Set plain text content
        msg.set_content(request.text or "Please view this email in an HTML-compatible client.")
        
        # Attach the HTML content
        msg.add_alternative(request.html, subtype='html')

        # Send the email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
            
        return {"success": True, "message": f"Email sent successfully to {request.to}"}
        
    except Exception as e:
        print(f"Error sending email: {e}")
        raise HTTPException(status_code=500, detail=str(e))
