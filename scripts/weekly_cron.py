import os
import sys
from datetime import datetime, timedelta
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import get_historical_data
from engines.email_reporter import send_weekly_report
from extractors.semrush_client import fetch_domain_analytics, fetch_backlinks, fetch_site_audit

def run_weekly_automation():
    print(f"[{datetime.now()}] Starting Weekly Growth Automation...")
    
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=7)
    
    print(f"Fetching data from {start_date} to {end_date}...")
    
    try:
        ga4_df, gsc_df, social_df, ga4_channels_df, gsc_queries_df, crm_df, semrush_df = get_historical_data(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
        
        # Aggregate the week's metrics from the database (GA4 / GSC)
        weekly_metrics = {
            'organic_sessions': int(ga4_df['sessions'].sum()) if not ga4_df.empty and 'sessions' in ga4_df.columns else 'N/A',
            'bounce_rate': 'N/A',
            'avg_time_on_page': 'N/A',
            
            'clicks': int(gsc_df['clicks'].sum()) if not gsc_df.empty and 'clicks' in gsc_df.columns else 'N/A',
            'impressions': int(gsc_df['impressions'].sum()) if not gsc_df.empty and 'impressions' in gsc_df.columns else 'N/A',
            'avg_ctr': 'N/A',
            'avg_keyword_position': 'N/A',
        }
        
        # Now, explicitly pull LIVE data from SEMrush API for the advanced metrics!
        print("Pulling live SEMrush Site Audit and Analytics data...")
        analytics = fetch_domain_analytics("inspiria.edu.in")
        backlinks = fetch_backlinks("inspiria.edu.in")
        site_audit = fetch_site_audit("30277688")
        
        # Merge SEMrush metrics into the dictionary
        weekly_metrics.update(analytics)
        weekly_metrics.update(backlinks)
        weekly_metrics.update(site_audit)
        
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
