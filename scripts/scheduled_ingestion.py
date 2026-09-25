import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from datetime import datetime, timedelta
from database.db_manager import init_db, upsert_ga4_data, upsert_gsc_data
from extractors.ga4_client import get_ga4_daily_data
from extractors.gsc_client import get_gsc_daily_data

def run_daily_ingestion():
    """Fetches the previous day's data and appends it to the SQLite database."""
    print("🚀 Running Daily Data Ingestion...")
    init_db()
    
    # We fetch 'yesterday' because today's data is usually incomplete
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    print(f"Target Date: {yesterday}")
    
    ga4_df = get_ga4_daily_data(yesterday, yesterday)
    if ga4_df is not None and not ga4_df.empty:
        upsert_ga4_data(ga4_df)
        print("✅ GA4 data ingested.")
        
    gsc_df = get_gsc_daily_data(yesterday, yesterday)
    if gsc_df is not None and not gsc_df.empty:
        upsert_gsc_data(gsc_df)
        print("✅ GSC data ingested.")
        
    from extractors.social_client import get_social_daily_data
    from database.db_manager import upsert_social_data
    
    social_df = get_social_daily_data(yesterday, yesterday)
    if social_df is not None and not social_df.empty:
        upsert_social_data(social_df)
        print("✅ Social data ingested.")
        
    print("🎉 Daily ingestion complete.")

if __name__ == "__main__":
    run_daily_ingestion()
