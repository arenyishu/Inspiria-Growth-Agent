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

def get_google_credentials(scopes=None):
    """
    Returns Google OAuth2 credentials.
    Tries Streamlit Secrets (for cloud), then falls back to local credentials.json.
    """
    try:
        import streamlit as st
        from google.oauth2 import service_account
        if "gcp_service_account" in st.secrets:
            creds_info = dict(st.secrets["gcp_service_account"])
            if scopes:
                return service_account.Credentials.from_service_account_info(creds_info, scopes=scopes)
            return service_account.Credentials.from_service_account_info(creds_info)
    except Exception:
        pass

    if GOOGLE_APPLICATION_CREDENTIALS and os.path.exists(GOOGLE_APPLICATION_CREDENTIALS):
        from google.oauth2 import service_account
        if scopes:
            return service_account.Credentials.from_service_account_file(GOOGLE_APPLICATION_CREDENTIALS, scopes=scopes)
        return service_account.Credentials.from_service_account_file(GOOGLE_APPLICATION_CREDENTIALS)
        
    return None
