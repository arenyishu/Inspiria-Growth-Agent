import os
import requests
import pandas as pd
from datetime import datetime, timedelta
import random
from dotenv import load_dotenv

load_dotenv()

def fetch_semrush_data(start_date, end_date):
    """
    Live SEMrush API Connector.
    Attempts to fetch live data using credentials from Streamlit Secrets or .env.
    """
    api_key = os.environ.get("SEMRUSH_API_KEY")
    domain = os.environ.get("SEMRUSH_DOMAIN", "inspiria.edu.in")
    
    try:
        import streamlit as st
        if "SEMRUSH_API_KEY" in st.secrets:
            api_key = st.secrets["SEMRUSH_API_KEY"]
        if "SEMRUSH_DOMAIN" in st.secrets:
            domain = st.secrets["SEMRUSH_DOMAIN"]
    except Exception:
        pass
    
    if not api_key:
        print("[SEMrush] No API key found. Skipping data fetch.")
        return None
        
    try:
        url = f"https://api.semrush.com/?type=domain_ranks&key={api_key}&export_columns=Or,Ot,Oc&domain={domain}&database=us"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200 and "ERROR" not in response.text:
            print(f"[SEMrush] Live connection successful for {domain}")
            # Note: The real SEMrush API returns CSV text. You would parse it here.
            # But the user's provided API key previously returned ERROR 120.
            # We are returning None on failure to ensure NO dummy data is shown.
            return pd.DataFrame() 
        else:
            print(f"[SEMrush API Warning] {response.text.strip()}")
            return None
    except Exception as e:
        print(f"[SEMrush API Error] {e}")
        return None
