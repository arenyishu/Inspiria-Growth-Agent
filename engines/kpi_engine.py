import pandas as pd

def calculate_percentage_change(current, previous):
    """Safely calculates percentage change between two numbers."""
    if previous == 0:
        return 100.0 if current > 0 else 0.0
    return ((current - previous) / previous) * 100

def compare_ga4_periods(df_current, df_previous):
    """Compares totals for GA4 data."""
    # Summing up totals across all channels for a high-level view
    cur_totals = df_current[['sessions', 'active_users', 'conversions', 'pageviews']].sum() if not df_current.empty else pd.Series({'sessions':0, 'active_users':0, 'conversions':0, 'pageviews':0})
    prev_totals = df_previous[['sessions', 'active_users', 'conversions', 'pageviews']].sum() if not df_previous.empty else pd.Series({'sessions':0, 'active_users':0, 'conversions':0, 'pageviews':0})

    metrics = {}
    for metric in ['sessions', 'active_users', 'conversions', 'pageviews']:
        cur = cur_totals.get(metric, 0)
        prev = prev_totals.get(metric, 0)
        change = calculate_percentage_change(cur, prev)
        metrics[metric] = {
            "current": int(cur),
            "previous": int(prev),
            "change_pct": round(change, 2)
        }
        
    return metrics

def compare_gsc_periods(df_current, df_previous):
    """Compares high-level GSC metrics."""
    cur_clicks = df_current['clicks'].sum() if not df_current.empty else 0
    prev_clicks = df_previous['clicks'].sum() if not df_previous.empty else 0
    
    cur_imp = df_current['impressions'].sum() if not df_current.empty else 0
    prev_imp = df_previous['impressions'].sum() if not df_previous.empty else 0
    
    metrics = {
        "clicks": {
            "current": int(cur_clicks),
            "previous": int(prev_clicks),
            "change_pct": round(calculate_percentage_change(cur_clicks, prev_clicks), 2)
        },
        "impressions": {
            "current": int(cur_imp),
            "previous": int(prev_imp),
            "change_pct": round(calculate_percentage_change(cur_imp, prev_imp), 2)
        }
    }
    return metrics
