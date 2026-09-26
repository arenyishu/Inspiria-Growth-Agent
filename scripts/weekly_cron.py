import os
import sys
from datetime import datetime, timedelta
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import get_historical_data, upsert_ga4_data, upsert_gsc_data, upsert_ga4_channels, upsert_gsc_queries
from extractors.ga4_client import get_ga4_daily_data, get_ga4_channels_data
from extractors.gsc_client import get_gsc_daily_data, get_gsc_queries_data
from engines.email_reporter import send_weekly_report
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import DateRange, Metric, RunReportRequest
from config.settings import get_google_credentials, GA4_PROPERTY_ID, GSC_SITE_URL
from googleapiclient.discovery import build
from extractors.pagespeed_client import fetch_core_web_vitals

def fetch_missing_metrics(start_date, end_date):
    new_metrics = {
        'bounce_rate': 'N/A', 'avg_time_on_page': 'N/A', 'avg_ctr': 'N/A', 'avg_keyword_position': 'N/A',
        'top_queries_html': '<li>No data</li>', 'top_pages_html': '<li>No data</li>'
    }
    ga4_creds = get_google_credentials()
    
    # 1. Fetch GA4 Extended
    if ga4_creds:
        try:
            client = BetaAnalyticsDataClient(credentials=ga4_creds)
            request = RunReportRequest(
                property=f"properties/{GA4_PROPERTY_ID}",
                metrics=[Metric(name="bounceRate"), Metric(name="averageSessionDuration")],
                date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            )
            resp = client.run_report(request)
            for row in resp.rows:
                new_metrics['bounce_rate'] = round(float(row.metric_values[0].value) * 100, 2)
                new_metrics['avg_time_on_page'] = round(float(row.metric_values[1].value), 1)
        except Exception as e:
            print(f"Failed GA4 extended: {e}")

    # 2. Fetch GSC Extended
    if ga4_creds:
        try:
            gsc_service = build('searchconsole', 'v1', credentials=ga4_creds)
            
            # Aggregate stats
            req_agg = {'startDate': start_date, 'endDate': end_date, 'dimensions': ['date']}
            res_agg = gsc_service.searchanalytics().query(siteUrl=GSC_SITE_URL, body=req_agg).execute()
            if 'rows' in res_agg:
                total_clicks = sum(r['clicks'] for r in res_agg['rows'])
                total_impressions = sum(r['impressions'] for r in res_agg['rows'])
                avg_position = sum(r['position'] for r in res_agg['rows']) / len(res_agg['rows'])
                if total_impressions > 0:
                    new_metrics['avg_ctr'] = round((total_clicks / total_impressions) * 100, 2)
                new_metrics['avg_keyword_position'] = round(avg_position, 1)
                
            # Top Queries
            req_q = {'startDate': start_date, 'endDate': end_date, 'dimensions': ['query'], 'rowLimit': 5}
            res_q = gsc_service.searchanalytics().query(siteUrl=GSC_SITE_URL, body=req_q).execute()
            if 'rows' in res_q:
                q_html = ""
                for r in res_q['rows']:
                    q_html += f"<li><b>{r['keys'][0]}</b>: {r['clicks']} clicks</li>"
                new_metrics['top_queries_html'] = q_html
                
            # Top Pages
            req_p = {'startDate': start_date, 'endDate': end_date, 'dimensions': ['page'], 'rowLimit': 5}
            res_p = gsc_service.searchanalytics().query(siteUrl=GSC_SITE_URL, body=req_p).execute()
            if 'rows' in res_p:
                p_html = ""
                for r in res_p['rows']:
                    path = r['keys'][0].replace('https://inspiria.edu.in', '')
                    p_html += f"<li><b>{path[:40]}...</b>: {r['clicks']} clicks</li>"
                new_metrics['top_pages_html'] = p_html
                
        except Exception as e:
            print(f"Failed GSC extended: {e}")
            
    return new_metrics

def run_weekly_automation():
    print(f"[{datetime.now()}] Starting Weekly Growth Automation...")
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=7)
    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')
    
    print(f"Ingesting latest data from {start_str} to {end_str}...")
    try:
        ga4_df = get_ga4_daily_data(start_str, end_str)
        if ga4_df is not None and not ga4_df.empty: upsert_ga4_data(ga4_df)
        
        ga4_ch_df = get_ga4_channels_data(start_str, end_str)
        if ga4_ch_df is not None and not ga4_ch_df.empty: upsert_ga4_channels(ga4_ch_df)
        
        gsc_df = get_gsc_daily_data(start_str, end_str)
        if gsc_df is not None and not gsc_df.empty: upsert_gsc_data(gsc_df)
        
        gsc_q_df = get_gsc_queries_data(start_str, end_str)
        if gsc_q_df is not None and not gsc_q_df.empty: upsert_gsc_queries(gsc_q_df)
        print("Data Ingestion complete.")
    except Exception as e:
        print(f"Ingestion warning: {e}")
    
    try:
        ga4_df, gsc_df, social_df, ga4_channels_df, gsc_queries_df, crm_df, semrush_df = get_historical_data(start_str, end_str)
        
        weekly_metrics = {
            'organic_sessions': int(ga4_df['sessions'].sum()) if not ga4_df.empty and 'sessions' in ga4_df.columns else 0,
            'pageviews': int(ga4_df['pageviews'].sum()) if not ga4_df.empty and 'pageviews' in ga4_df.columns else 0,
            'clicks': int(gsc_df['clicks'].sum()) if not gsc_df.empty and 'clicks' in gsc_df.columns else 0,
            'impressions': int(gsc_df['impressions'].sum()) if not gsc_df.empty and 'impressions' in gsc_df.columns else 0,
            'social_followers': int(social_df['followers'].max()) if not social_df.empty and 'followers' in social_df.columns else 0,
            'social_reach': int(social_df['reach'].sum()) if not social_df.empty and 'reach' in social_df.columns else 0,
            'social_engagement': int(social_df['engagement'].sum()) if not social_df.empty and 'engagement' in social_df.columns else 0,
        }
        
        print("Pulling live PageSpeed Insights data...")
        pagespeed = fetch_core_web_vitals("https://inspiria.edu.in")
        weekly_metrics.update(pagespeed)
        
        print("Pulling missing metrics from Google APIs...")
        extended = fetch_missing_metrics(start_str, end_str)
        weekly_metrics.update(extended)
        
        weekly_metrics['mobile_usability_issues'] = 'N/A (API Restricted)'
        
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
