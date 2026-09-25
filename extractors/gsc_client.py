from googleapiclient.discovery import build
from google.oauth2 import service_account
import pandas as pd
from config.settings import GSC_SITE_URL, GOOGLE_APPLICATION_CREDENTIALS
import os

def get_gsc_data(start_date, end_date):
    """Fetches search query data from Google Search Console."""
    
    if not os.path.exists(GOOGLE_APPLICATION_CREDENTIALS):
        print(f"❌ Error: {GOOGLE_APPLICATION_CREDENTIALS} not found.")
        return None

    print(f"Fetching GSC Data for {GSC_SITE_URL} ({start_date} to {end_date})...")

    try:
        # Authenticate
        credentials = service_account.Credentials.from_service_account_file(
            GOOGLE_APPLICATION_CREDENTIALS,
            scopes=['https://www.googleapis.com/auth/webmasters.readonly']
        )
        
        service = build('searchconsole', 'v1', credentials=credentials)
        
        # Build the request body
        request = {
            'startDate': start_date, # Format: 'YYYY-MM-DD'
            'endDate': end_date,
            'dimensions': ['query', 'page'],
            'rowLimit': 500 # Adjust as needed for the MVP
        }
        
        response = service.searchanalytics().query(
            siteUrl=GSC_SITE_URL, 
            body=request
        ).execute()
        
        # Convert to DataFrame
        data = []
        if 'rows' in response:
            for row in response['rows']:
                data.append({
                    "query": row['keys'][0],
                    "page": row['keys'][1],
                    "clicks": row['clicks'],
                    "impressions": row['impressions'],
                    "ctr": row['ctr'],
                    "position": row['position']
                })
                
        df = pd.DataFrame(data)
        return df

    except Exception as e:
        print(f"❌ GSC API Error: {e}")
        return None

def get_gsc_daily_data(start_date, end_date):
    """Fetches daily aggregate search data from Google Search Console."""
    if not os.path.exists(GOOGLE_APPLICATION_CREDENTIALS):
        return None

    try:
        credentials = service_account.Credentials.from_service_account_file(
            GOOGLE_APPLICATION_CREDENTIALS,
            scopes=['https://www.googleapis.com/auth/webmasters.readonly']
        )
        service = build('searchconsole', 'v1', credentials=credentials)
        
        request = {
            'startDate': start_date,
            'endDate': end_date,
            'dimensions': ['date'], # Group by date instead of query/page
            'rowLimit': 10000
        }
        
        response = service.searchanalytics().query(siteUrl=GSC_SITE_URL, body=request).execute()
        
        data = []
        if 'rows' in response:
            for row in response['rows']:
                data.append({
                    "date": row['keys'][0],
                    "clicks": row['clicks'],
                    "impressions": row['impressions']
                })
                
        return pd.DataFrame(data)
    except Exception as e:
        print(f"Error fetching daily GSC data: {e}")
        return None

def get_gsc_queries_data(start_date, end_date):
    """Fetches daily query data from Google Search Console."""
    if not os.path.exists(GOOGLE_APPLICATION_CREDENTIALS):
        return None

    try:
        credentials = service_account.Credentials.from_service_account_file(
            GOOGLE_APPLICATION_CREDENTIALS,
            scopes=['https://www.googleapis.com/auth/webmasters.readonly']
        )
        service = build('searchconsole', 'v1', credentials=credentials)
        
        request = {
            'startDate': start_date,
            'endDate': end_date,
            'dimensions': ['date', 'query'],
            'rowLimit': 5000
        }
        
        response = service.searchanalytics().query(siteUrl=GSC_SITE_URL, body=request).execute()
        
        data = []
        if 'rows' in response:
            for row in response['rows']:
                data.append({
                    "date": row['keys'][0],
                    "keys": row['keys'][1],
                    "clicks": row['clicks'],
                    "impressions": row['impressions']
                })
                
        return pd.DataFrame(data)
    except Exception as e:
        print(f"Error fetching queries GSC data: {e}")
        return None

if __name__ == "__main__":
    # Test dates (Format must be YYYY-MM-DD for GSC)
    from datetime import datetime, timedelta
    end = datetime.now().strftime('%Y-%m-%d')
    start = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    
    df = get_gsc_data(start, end)
    if df is not None:
        print("✅ GSC Data Fetched Successfully:")
        print(df.head())
