import os
import sys
from datetime import datetime, timedelta
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import get_historical_data
from engines.email_reporter import send_weekly_report

# We import the credentials configuration to make direct calls for the missing fields
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import DateRange, Metric, RunReportRequest, Dimension
from config.settings import get_google_credentials, GA4_PROPERTY_ID, GSC_SITE_URL
from googleapiclient.discovery import build

def fetch_missing_metrics(start_date, end_date):
    """Fetches metrics that aren't stored in our current daily database tables."""
    new_metrics = {
        'bounce_rate': 'N/A',
        'avg_time_on_page': 'N/A',
        'avg_ctr': 'N/A',
        'avg_keyword_position': 'N/A'
    }
    
    # 1. Fetch from GA4
    ga4_creds = get_google_credentials()
    if ga4_creds:
        try:
            client = BetaAnalyticsDataClient(credentials=ga4_creds)
            request = RunReportRequest(
                property=f"properties/{GA4_PROPERTY_ID}",
                metrics=[
                    Metric(name="bounceRate"),
                    Metric(name="averageSessionDuration")
                ],
                date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            )
            resp = client.run_report(request)
            for row in resp.rows:
                new_metrics['bounce_rate'] = round(float(row.metric_values[0].value) * 100, 2)
                new_metrics['avg_time_on_page'] = round(float(row.metric_values[1].value), 1)
        except Exception as e:
            print(f"Failed to fetch GA4 extended metrics: {e}")

    # 2. Fetch from GSC
    if ga4_creds:
        try:
            gsc_service = build('searchconsole', 'v1', credentials=ga4_creds)
            request = {
                'startDate': start_date,
                'endDate': end_date,
                'dimensions': ['date']
            }
            response = gsc_service.searchanalytics().query(
                siteUrl=GSC_SITE_URL, body=request
            ).execute()
            
            if 'rows' in response:
                total_clicks = sum(row['clicks'] for row in response['rows'])
                total_impressions = sum(row['impressions'] for row in response['rows'])
                avg_position = sum(row['position'] for row in response['rows']) / len(response['rows'])
                
                if total_impressions > 0:
                    new_metrics['avg_ctr'] = round((total_clicks / total_impressions) * 100, 2)
                new_metrics['avg_keyword_position'] = round(avg_position, 1)
        except Exception as e:
            print(f"Failed to fetch GSC extended metrics: {e}")
            
    return new_metrics

def run_weekly_automation():
    print(f"[{datetime.now()}] Starting Weekly Growth Automation...")
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=7)
    
    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')
    
    try:
        ga4_df, gsc_df, social_df, ga4_channels_df, gsc_queries_df, crm_df, semrush_df = get_historical_data(start_str, end_str)
        
        # Aggregate database metrics
        weekly_metrics = {
            'organic_sessions': int(ga4_df['sessions'].sum()) if not ga4_df.empty and 'sessions' in ga4_df.columns else 0,
            'pageviews': int(ga4_df['pageviews'].sum()) if not ga4_df.empty and 'pageviews' in ga4_df.columns else 0,
            'clicks': int(gsc_df['clicks'].sum()) if not gsc_df.empty and 'clicks' in gsc_df.columns else 0,
            'impressions': int(gsc_df['impressions'].sum()) if not gsc_df.empty and 'impressions' in gsc_df.columns else 0,
            'social_followers': int(social_df['followers'].max()) if not social_df.empty and 'followers' in social_df.columns else 0,
            'social_reach': int(social_df['reach'].sum()) if not social_df.empty and 'reach' in social_df.columns else 0,
            'social_engagement': int(social_df['engagement'].sum()) if not social_df.empty and 'engagement' in social_df.columns else 0,
        }
        
        # Fetch the missing on-page fields directly from Google APIs
        print("Pulling missing metrics from Google APIs...")
        extended = fetch_missing_metrics(start_str, end_str)
        weekly_metrics.update(extended)
        
        # NOTE: SEMrush fields were removed to keep the report clean and strictly Google/Social based.
        
        print("Data aggregated successfully. Triggering Email Reporter...")
        success = send_weekly_report(weekly_metrics)
        if success:
            print("Weekly Automation completed successfully!")
        else:
            print("Weekly Automation finished, but email failed to send.")
            
    except Exception as e:
        print(f"CRITICAL ERROR in weekly automation: {e}")

if __name__ == "__main__":
    run_weekly_automation()
