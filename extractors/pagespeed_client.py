import requests
import os
import streamlit as st

def fetch_core_web_vitals(url="https://inspiria.edu.in"):
    # Try to get API key from streamlit secrets, then environment
    api_key = None
    try:
        api_key = st.secrets.get("PAGESPEED_API_KEY")
    except:
        pass
    if not api_key:
        api_key = os.environ.get("PAGESPEED_API_KEY", "")

    # Build URL
    if api_key:
        api_url = f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url={url}&strategy=mobile&key={api_key}"
    else:
        api_url = f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url={url}&strategy=mobile"

    try:
        resp = requests.get(api_url, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            metrics = data.get('originLoadingExperience', {}).get('metrics', {})
            
            lcp = metrics.get('LARGEST_CONTENTFUL_PAINT_MS', {}).get('percentile', 'N/A')
            inp = metrics.get('INTERACTION_TO_NEXT_PAINT', {}).get('percentile', 'N/A')
            cls_score = metrics.get('CUMULATIVE_LAYOUT_SHIFT_SCORE', {}).get('percentile', 'N/A')
            
            if lcp != 'N/A': lcp = f"{lcp / 1000}s"
            if inp != 'N/A': inp = f"{inp}ms"
            if cls_score != 'N/A': cls_score = str(cls_score / 100)
            
            return {
                'avg_lcp': lcp,
                'avg_inp': inp,
                'avg_cls': cls_score
            }
        else:
            print(f"PageSpeed API returned status {resp.status_code}")
    except Exception as e:
        print(f"PageSpeed API Error: {e}")
        
    return {'avg_lcp': 'N/A', 'avg_inp': 'N/A', 'avg_cls': 'N/A'}
