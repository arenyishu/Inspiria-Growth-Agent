import os
import requests
import pandas as pd
from datetime import datetime, timedelta
import io

def get_api_key():
    try:
        import streamlit as st
        if "SEMRUSH_API_KEY" in st.secrets:
            return st.secrets["SEMRUSH_API_KEY"]
    except Exception:
        pass
    return os.environ.get("SEMRUSH_API_KEY")

def fetch_domain_analytics(domain="inspiria.edu.in"):
    api_key = get_api_key()
    if not api_key: return {}
    
    url = f"https://api.semrush.com/?type=domain_ranks&key={api_key}&export_columns=Dn,Or,Ot,Oc&domain={domain}&database=us"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200 and "ERROR" not in resp.text:
            df = pd.read_csv(io.StringIO(resp.text), sep=';')
            if not df.empty:
                row = df.iloc[0]
                return {
                    'organic_keywords': int(row.get('Organic Keywords', 0)),
                    'organic_traffic': int(row.get('Organic Traffic', 0))
                }
    except Exception as e:
        print(f"SEMrush Domain API Error: {e}")
    return {}

def fetch_backlinks(domain="inspiria.edu.in"):
    api_key = get_api_key()
    if not api_key: return {}
    
    url = f"https://api.semrush.com/analytics/v1/?type=backlinks_overview&key={api_key}&target={domain}&target_type=root_domain&export_columns=total,domains_num,score"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200 and "ERROR" not in resp.text:
            df = pd.read_csv(io.StringIO(resp.text), sep=';')
            if not df.empty:
                row = df.iloc[0]
                return {
                    'total_backlinks': int(row.get('total', 0)),
                    'referring_domains': int(row.get('domains_num', 0)),
                    'avg_dr': int(row.get('score', 0))
                }
    except Exception as e:
        print(f"SEMrush Backlinks API Error: {e}")
    return {}

def fetch_site_audit(project_id="30277688"):
    api_key = get_api_key()
    if not api_key: return {}
    
    url = f"https://api.semrush.com/reports/v1/projects/{project_id}/siteaudit/info?key={api_key}"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200 and "ERROR" not in resp.text:
            data = resp.json()
            return {
                'pages_crawled': data.get('pages_crawled', 'N/A'),
                'broken_links': data.get('broken_links', 'N/A'),
                'server_errors_5xx': data.get('errors_5xx', 'N/A'),
                'duplicate_pages': data.get('duplicate_pages', 'N/A'),
                'tech_seo_score': data.get('health_score', 'N/A')
            }
    except Exception as e:
        print(f"SEMrush Site Audit API Error: {e}")
    return {}
