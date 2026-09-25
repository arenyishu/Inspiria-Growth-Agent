import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Keys and IDs
GA4_PROPERTY_ID = os.getenv("GA4_PROPERTY_ID")
GSC_SITE_URL = os.getenv("GSC_SITE_URL")
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Rule Thresholds for Detection Engine (from Product Requirements)
THRESHOLDS = {
    "STRONG_DECLINE": -20.0,
    "WARNING_DECLINE": -10.0,
    "GROWTH": 10.0
}
