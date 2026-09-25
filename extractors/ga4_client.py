from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Metric,
    RunReportRequest,
)
import pandas as pd
from config.settings import GA4_PROPERTY_ID, GOOGLE_APPLICATION_CREDENTIALS
import os

def get_ga4_data(start_date="7daysAgo", end_date="today"):
    """Fetches key metrics from GA4 for a given date range."""
    
    # Ensure credentials exist
    if not os.path.exists(GOOGLE_APPLICATION_CREDENTIALS):
        print(f"❌ Error: {GOOGLE_APPLICATION_CREDENTIALS} not found.")
        print("Please make sure you downloaded your Service Account JSON and named it 'credentials.json'")
        return None

    print(f"Fetching GA4 Data for property {GA4_PROPERTY_ID} ({start_date} to {end_date})...")
    
    try:
        # Using the environment variable GOOGLE_APPLICATION_CREDENTIALS automatically authenticates
        client = BetaAnalyticsDataClient()

        request = RunReportRequest(
            property=f"properties/{GA4_PROPERTY_ID}",
            dimensions=[Dimension(name="sessionDefaultChannelGroup")],
            metrics=[
                Metric(name="sessions"),
                Metric(name="activeUsers"),
                Metric(name="conversions"),
                Metric(name="screenPageViews")
            ],
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
        )

        response = client.run_report(request)
        
        # Convert to Pandas DataFrame for easier processing later
        data = []
        for row in response.rows:
            data.append({
                "channel": row.dimension_values[0].value,
                "sessions": int(row.metric_values[0].value),
                "active_users": int(row.metric_values[1].value),
                "conversions": int(float(row.metric_values[2].value)),
                "pageviews": int(row.metric_values[3].value)
            })
            
        df = pd.DataFrame(data)
        return df

    except Exception as e:
        print(f"❌ GA4 API Error: {e}")
        return None

def get_ga4_daily_data(start_date, end_date):
    """Fetches daily metrics from GA4 for database storage."""
    if not os.path.exists(GOOGLE_APPLICATION_CREDENTIALS):
        return None

    try:
        client = BetaAnalyticsDataClient()
        request = RunReportRequest(
            property=f"properties/{GA4_PROPERTY_ID}",
            dimensions=[Dimension(name="date")],
            metrics=[
                Metric(name="sessions"),
                Metric(name="activeUsers"),
                Metric(name="conversions"),
                Metric(name="screenPageViews")
            ],
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
        )

        response = client.run_report(request)
        
        data = []
        for row in response.rows:
            # GA4 returns date as YYYYMMDD, convert to YYYY-MM-DD
            raw_date = row.dimension_values[0].value
            formatted_date = f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:]}"
            
            data.append({
                "date": formatted_date,
                "sessions": int(row.metric_values[0].value),
                "active_users": int(row.metric_values[1].value),
                "conversions": int(float(row.metric_values[2].value)),
                "pageviews": int(row.metric_values[3].value)
            })
            
        return pd.DataFrame(data)
    except Exception as e:
        print(f"Error fetching daily GA4 data: {e}")
        return None

def get_ga4_channels_data(start_date, end_date):
    """Fetches daily metrics by channel from GA4 for database storage."""
    if not os.path.exists(GOOGLE_APPLICATION_CREDENTIALS):
        return None

    try:
        client = BetaAnalyticsDataClient()
        request = RunReportRequest(
            property=f"properties/{GA4_PROPERTY_ID}",
            dimensions=[Dimension(name="date"), Dimension(name="sessionDefaultChannelGroup")],
            metrics=[
                Metric(name="sessions")
            ],
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
        )

        response = client.run_report(request)
        
        data = []
        for row in response.rows:
            raw_date = row.dimension_values[0].value
            formatted_date = f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:]}"
            
            data.append({
                "date": formatted_date,
                "sessionDefaultChannelGroup": row.dimension_values[1].value,
                "sessions": int(row.metric_values[0].value)
            })
            
        return pd.DataFrame(data)
    except Exception as e:
        print(f"Error fetching channel GA4 data: {e}")
        return None

if __name__ == "__main__":
    df = get_ga4_data()
    if df is not None:
        print("✅ GA4 Data Fetched Successfully:")
        print(df)
