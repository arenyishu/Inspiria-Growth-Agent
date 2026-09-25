import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from database.db_manager import init_db, upsert_ga4_data, upsert_gsc_data
from extractors.ga4_client import get_ga4_daily_data
from extractors.gsc_client import get_gsc_daily_data
import time

def backfill_history(years=3):
    print("🚀 Starting Historical Backfill...")
    init_db()
    
    end_date = datetime.now()
    start_date = end_date - relativedelta(years=years)
    
    print(f"Target Range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print("Fetching in 1-month chunks to avoid API limits...")
    
    current_chunk_start = start_date
    
    while current_chunk_start < end_date:
        current_chunk_end = min(current_chunk_start + relativedelta(months=1) - timedelta(days=1), end_date)
        
        start_str = current_chunk_start.strftime('%Y-%m-%d')
        end_str = current_chunk_end.strftime('%Y-%m-%d')
        
        print(f"\nProcessing Chunk: {start_str} to {end_str}")
        
        # 1. GA4
        try:
            ga4_df = get_ga4_daily_data(start_str, end_str)
            if ga4_df is not None and not ga4_df.empty:
                upsert_ga4_data(ga4_df)
                print(f"  ✅ Saved {len(ga4_df)} days of GA4 data.")
            else:
                print("  ⚠️ No GA4 data for this period.")
        except Exception as e:
            print(f"  ❌ Failed to fetch GA4: {e}")
            
        time.sleep(1) # Respect rate limits
        
        # 1b. GA4 Channels
        try:
            from extractors.ga4_client import get_ga4_channels_data
            from database.db_manager import upsert_ga4_channels
            ga4_ch_df = get_ga4_channels_data(start_str, end_str)
            if ga4_ch_df is not None and not ga4_ch_df.empty:
                upsert_ga4_channels(ga4_ch_df)
                print(f"  ✅ Saved {len(ga4_ch_df)} rows of GA4 channel data.")
        except Exception as e:
            print(f"  ❌ Failed to fetch GA4 channels: {e}")
            
        time.sleep(1)
            
        # 2. GSC
        try:
            gsc_df = get_gsc_daily_data(start_str, end_str)
            if gsc_df is not None and not gsc_df.empty:
                upsert_gsc_data(gsc_df)
                print(f"  ✅ Saved {len(gsc_df)} days of GSC data.")
            else:
                print("  ⚠️ No GSC data for this period (Google Search Console only keeps 16 months).")
        except Exception as e:
            print(f"  ❌ Failed to fetch GSC: {e}")
            
        time.sleep(1) # Respect rate limits
        
        # 2b. GSC Queries
        try:
            from extractors.gsc_client import get_gsc_queries_data
            from database.db_manager import upsert_gsc_queries
            gsc_q_df = get_gsc_queries_data(start_str, end_str)
            if gsc_q_df is not None and not gsc_q_df.empty:
                upsert_gsc_queries(gsc_q_df)
                print(f"  ✅ Saved {len(gsc_q_df)} rows of GSC query data.")
        except Exception as e:
            print(f"  ❌ Failed to fetch GSC queries: {e}")
            
        time.sleep(1)

        # 3. Social Media
        from extractors.social_client import get_social_daily_data
        from database.db_manager import upsert_social_data
        
        try:
            social_df = get_social_daily_data(start_str, end_str)
            if social_df is not None and not social_df.empty:
                upsert_social_data(social_df)
                print(f"  ✅ Saved {len(social_df)} days of Social Media data.")
        except Exception as e:
            print(f"  ❌ Failed to fetch Social Data: {e}")
            
        current_chunk_start = current_chunk_end + timedelta(days=1)
        
    print("\n🎉 Backfill Complete! Data safely warehoused in SQLite.")

if __name__ == "__main__":
    backfill_history()
