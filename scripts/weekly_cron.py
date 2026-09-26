import os
import sys
from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy import create_engine
import importlib

# Add root directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import get_historical_data
from engines.email_reporter import send_weekly_report

def run_weekly_automation():
    print(f"[{datetime.now()}] Starting Weekly Growth Automation...")
    
    # 1. We assume the APIs have pulled the latest data via standard backfills.
    # To keep this script clean, it will query the database for the last 7 days of data.
    
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=7)
    
    print(f"Fetching data from {start_date} to {end_date}...")
    
    try:
        ga4_df, gsc_df, social_df, ga4_channels_df, gsc_queries_df, crm_df, semrush_df = get_historical_data(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
        
        # Aggregate the week's metrics
        weekly_metrics = {
            'organic_sessions': int(ga4_df['organic_sessions'].sum()) if not ga4_df.empty else 0,
            'bounce_rate': round(ga4_df['bounce_rate'].mean(), 2) if not ga4_df.empty else 0.0,
            'avg_time_on_page': round(ga4_df['avg_time_on_page'].mean(), 1) if not ga4_df.empty else 0.0,
            
            'clicks': int(gsc_df['clicks'].sum()) if not gsc_df.empty else 0,
            'impressions': int(gsc_df['impressions'].sum()) if not gsc_df.empty else 0,
            'avg_ctr': round(gsc_df['ctr'].mean() * 100, 2) if not gsc_df.empty else 0.0,
            'avg_keyword_position': round(gsc_df['position'].mean(), 1) if not gsc_df.empty else 0.0,
            
            'avg_dr': int(semrush_df['domain_authority'].mean()) if not semrush_df.empty else "N/A",
            'total_backlinks': int(semrush_df['backlinks'].mean()) if not semrush_df.empty else "N/A",
            'keywords_top_10': int(semrush_df['organic_keywords'].mean()) if not semrush_df.empty else "N/A"
        }
        
        print("Data aggregated successfully. Triggering Email Reporter...")
        
        # Send Email
        success = send_weekly_report(weekly_metrics)
        if success:
            print("Weekly Automation completed successfully!")
        else:
            print("Weekly Automation finished, but email failed to send.")
            
    except Exception as e:
        print(f"CRITICAL ERROR in weekly automation: {e}")

if __name__ == "__main__":
    run_weekly_automation()
