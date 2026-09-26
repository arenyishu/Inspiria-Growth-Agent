import pandas as pd
import os
import streamlit as st
import psycopg2
import urllib.parse
from dotenv import load_dotenv

load_dotenv()

try:
    # First try Streamlit Secrets (for Cloud)
    if 'SUPABASE_URI' in st.secrets:
        SUPABASE_URI = st.secrets['SUPABASE_URI']
    # Then try local environment variables (for local development)
    else:
        SUPABASE_URI = os.environ.get('SUPABASE_URI')
except Exception:
    SUPABASE_URI = os.environ.get('SUPABASE_URI')

if not SUPABASE_URI:
    print("WARNING: SUPABASE_URI is not set! Database connections will fail.")

def get_connection():
    return psycopg2.connect(SUPABASE_URI)


def init_db():
    """Initializes the SQLite database with tables for GA4, GSC, and Social daily metrics."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Table for GA4 Daily Aggregates
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS ga4_daily (
        date TEXT PRIMARY KEY,
        sessions INTEGER,
        active_users INTEGER,
        conversions INTEGER,
        pageviews INTEGER
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS ga4_channels (
        date TEXT,
        channel TEXT,
        sessions INTEGER,
        PRIMARY KEY (date, channel)
    )
    ''')
    
    # Table for GSC Daily Aggregates
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS gsc_daily (
        date TEXT PRIMARY KEY,
        clicks INTEGER,
        impressions INTEGER
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS gsc_queries (
        date TEXT,
        query TEXT,
        clicks INTEGER,
        impressions INTEGER,
        PRIMARY KEY (date, query)
    )
    ''')
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS gsc_pages (
        date TEXT,
        page TEXT,
        clicks INTEGER,
        impressions INTEGER,
        PRIMARY KEY (date, page)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS gsc_countries (
        date TEXT,
        country TEXT,
        clicks INTEGER,
        impressions INTEGER,
        PRIMARY KEY (date, country)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS gsc_devices (
        date TEXT,
        device TEXT,
        clicks INTEGER,
        impressions INTEGER,
        PRIMARY KEY (date, device)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS gsc_search_appearance (
        date TEXT,
        appearance TEXT,
        clicks INTEGER,
        impressions INTEGER,
        PRIMARY KEY (date, appearance)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ga4_gsc_landing_pages (
        date TEXT,
        landing_page TEXT,
        clicks INTEGER,
        impressions INTEGER,
        ctr REAL,
        position REAL,
        active_users INTEGER,
        engaged_sessions INTEGER,
        engagement_rate REAL,
        avg_engagement_time REAL,
        event_count INTEGER,
        key_events INTEGER,
        PRIMARY KEY (date, landing_page)
    )
    """)



    # Table for Social Media Daily Aggregates
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS social_daily (
        date TEXT PRIMARY KEY,
        total_followers INTEGER,
        daily_reach INTEGER,
        daily_engagement INTEGER
    )
    ''')
    
    # Table for CRM Conversions (Pipeline)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS crm_conversions (
        conversion_id TEXT PRIMARY KEY,
        date TEXT,
        landing_page TEXT,
        source TEXT,
        qualified TEXT,
        customer TEXT,
        revenue REAL
    )
    ''')
    
    # Table for Action Register (Tasks)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS action_register (
        task_id SERIAL PRIMARY KEY,
        task_name TEXT,
        status TEXT,
        priority TEXT,
        created_at TEXT
    )
    ''')

    # Table for SEMrush Daily Metrics
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS semrush_daily (
        date TEXT PRIMARY KEY,
        authority_score INTEGER,
        total_backlinks INTEGER,
        referring_domains INTEGER,
        organic_keywords INTEGER,
        traffic_cost REAL
    )
    ''')

    conn.commit()
    conn.close()

def upsert_ga4_data(df):
    """Inserts or updates GA4 data into the database."""
    if df is None or df.empty:
        return
        
    conn = get_connection()
    for col in ['date', 'sessions', 'active_users', 'conversions', 'pageviews']:
        if col not in df.columns:
            df[col] = 0
            
    df = df[['date', 'sessions', 'active_users', 'conversions', 'pageviews']]
    
    for _, row in df.iterrows():
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO ga4_daily (date, sessions, active_users, conversions, pageviews)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT(date) DO UPDATE SET
            sessions=excluded.sessions,
            active_users=excluded.active_users,
            conversions=excluded.conversions,
            pageviews=excluded.pageviews
        ''', (row['date'], int(row['sessions']), int(row['active_users']), int(row['conversions']), int(row['pageviews'])))
    
    conn.commit()
    conn.close()

def upsert_ga4_channels(df):
    if df is None or df.empty: return
    conn = get_connection()
    for _, row in df.iterrows():
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO ga4_channels (date, channel, sessions)
        VALUES (%s, %s, %s)
        ON CONFLICT(date, channel) DO UPDATE SET sessions=excluded.sessions
        ''', (row['date'], str(row['sessionDefaultChannelGroup']), int(row['sessions'])))
    conn.commit()
    conn.close()

def upsert_gsc_data(df):
    """Inserts or updates GSC data into the database."""
    if df is None or df.empty:
        return
        
    conn = get_connection()
    for col in ['date', 'clicks', 'impressions']:
        if col not in df.columns:
            df[col] = 0
            
    df = df[['date', 'clicks', 'impressions']]
    
    for _, row in df.iterrows():
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO gsc_daily (date, clicks, impressions)
        VALUES (%s, %s, %s)
        ON CONFLICT(date) DO UPDATE SET
            clicks=excluded.clicks,
            impressions=excluded.impressions
        ''', (row['date'], int(row['clicks']), int(row['impressions'])))
    
    conn.commit()
    conn.close()

def upsert_gsc_queries(df):
    if df is None or df.empty: return
    conn = get_connection()
    for _, row in df.iterrows():
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO gsc_queries (date, query, clicks, impressions)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT(date, query) DO UPDATE SET
            clicks=excluded.clicks,
            impressions=excluded.impressions
        ''', (row['date'], str(row['keys']), int(row['clicks']), int(row['impressions'])))
    conn.commit()
    conn.close()

def upsert_social_data(df):
    """Inserts or updates Social Media data into the database."""
    if df is None or df.empty:
        return
        
    conn = get_connection()
    for col in ['date', 'total_followers', 'daily_reach', 'daily_engagement']:
        if col not in df.columns:
            df[col] = 0
            
    df = df[['date', 'total_followers', 'daily_reach', 'daily_engagement']]
    
    for _, row in df.iterrows():
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO social_daily (date, total_followers, daily_reach, daily_engagement)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT(date) DO UPDATE SET
            total_followers=excluded.total_followers,
            daily_reach=excluded.daily_reach,
            daily_engagement=excluded.daily_engagement
        ''', (row['date'], int(row['total_followers']), int(row['daily_reach']), int(row['daily_engagement'])))
    
    conn.commit()
    conn.close()

def upsert_crm_conversions(df):
    if df is None or df.empty: return
    conn = get_connection()
    for _, row in df.iterrows():
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO crm_conversions (conversion_id, date, landing_page, source, qualified, customer, revenue)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT(conversion_id) DO UPDATE SET
            qualified=excluded.qualified, customer=excluded.customer, revenue=excluded.revenue
        ''', (str(row.get('Conversion ID', '')), str(row.get('Conversion Date', '')), str(row.get('Landing Page', '')), str(row.get('Source', '')), str(row.get('Qualified%s', '')), str(row.get('Customer%s', '')), float(row.get('Revenue / Pipeline Value', 0))))
    conn.commit()
    conn.close()

def add_action_task(task_name, priority):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO action_register (task_name, status, priority, created_at) VALUES (%s, 'Planned', %s, CURRENT_DATE)", (task_name, priority))
    conn.commit()
    conn.close()

def get_action_tasks():
    conn = get_connection()
    from sqlalchemy import create_engine
    engine = create_engine(SUPABASE_URI.replace("postgresql://", "postgresql+psycopg2://"))
    df = pd.read_sql_query("SELECT * FROM action_register ORDER BY task_id DESC", engine)
    conn.close()
    return df

def update_action_task(task_id, status):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE action_register SET status = %s WHERE task_id = %s", (status, task_id))
    conn.commit()
    conn.close()

def upsert_semrush_data(df):
    conn = get_connection()
    cursor = conn.cursor()
    for _, row in df.iterrows():
        cursor.execute('''
        INSERT INTO semrush_daily (date, authority_score, total_backlinks, referring_domains, organic_keywords, traffic_cost)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT(date) DO UPDATE SET
            authority_score=excluded.authority_score,
            total_backlinks=excluded.total_backlinks,
            referring_domains=excluded.referring_domains,
            organic_keywords=excluded.organic_keywords,
            traffic_cost=excluded.traffic_cost
        ''', (
            row['date'], 
            row['authority_score'], 
            row['total_backlinks'], 
            row['referring_domains'], 
            row['organic_keywords'], 
            row['traffic_cost']
        ))
    conn.commit()
    conn.close()

def get_historical_data(start_date, end_date):
    from sqlalchemy import create_engine
    engine = create_engine(SUPABASE_URI.replace('postgresql://', 'postgresql+psycopg2://'))
    ga4_df = pd.read_sql_query(
        "SELECT * FROM ga4_daily WHERE date >= %(start)s AND date <= %(end)s ORDER BY date ASC", 
        engine, params={"start": start_date, "end": end_date}
    )
    
    gsc_df = pd.read_sql_query(
        "SELECT * FROM gsc_daily WHERE date >= %(start)s AND date <= %(end)s ORDER BY date ASC", 
        engine, params={"start": start_date, "end": end_date}
    )
    
    social_df = pd.read_sql_query(
        "SELECT * FROM social_daily WHERE date >= %(start)s AND date <= %(end)s ORDER BY date ASC", 
        engine, params={"start": start_date, "end": end_date}
    )

    ga4_channels_df = pd.read_sql_query(
        "SELECT * FROM ga4_channels WHERE date >= %(start)s AND date <= %(end)s ORDER BY date ASC", 
        engine, params={"start": start_date, "end": end_date}
    )

    gsc_queries_df = pd.read_sql_query(
        "SELECT * FROM gsc_queries WHERE date >= %(start)s AND date <= %(end)s ORDER BY date ASC", 
        engine, params={"start": start_date, "end": end_date}
    )

    crm_df = pd.read_sql_query(
        "SELECT * FROM crm_conversions WHERE date >= %(start)s AND date <= %(end)s ORDER BY date ASC", 
        engine, params={"start": start_date, "end": end_date}
    )

    semrush_df = pd.read_sql_query(
        "SELECT * FROM semrush_daily WHERE date >= %(start)s AND date <= %(end)s ORDER BY date ASC", 
        engine, params={"start": start_date, "end": end_date}
    )
    
    return ga4_df, gsc_df, social_df, ga4_channels_df, gsc_queries_df, crm_df, semrush_df
def save_ai_insights(insights_dict):
    conn = get_connection()
    if not conn: return False
    try:
        import json
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO ai_insights (insights) VALUES (%s)",
                (json.dumps(insights_dict),)
            )
        conn.commit()
        return True
    except Exception as e:
        print(f"Error saving AI insights: {e}")
        return False
    finally:
        conn.close()

def get_latest_ai_insights():
    conn = get_connection()
    if not conn: return None
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT insights FROM ai_insights ORDER BY created_at DESC LIMIT 1")
            row = cur.fetchone()
            if row:
                return row[0]
        return None
    except Exception as e:
        print(f"Error getting AI insights: {e}")
        return None
    finally:
        conn.close()

def upsert_gsc_pages(df):
    if df is None or df.empty: return
    conn = get_connection()
    cursor = conn.cursor()
    for _, row in df.iterrows():
        cursor.execute("""
        INSERT INTO gsc_pages (date, page, clicks, impressions)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT(date, page) DO UPDATE SET
            clicks=excluded.clicks,
            impressions=excluded.impressions
        """, (row['date'], str(row['page']), int(row['clicks']), int(row['impressions'])))
    conn.commit()
    conn.close()

def upsert_gsc_countries(df):
    if df is None or df.empty: return
    conn = get_connection()
    cursor = conn.cursor()
    for _, row in df.iterrows():
        cursor.execute("""
        INSERT INTO gsc_countries (date, country, clicks, impressions)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT(date, country) DO UPDATE SET
            clicks=excluded.clicks,
            impressions=excluded.impressions
        """, (row['date'], str(row['country']), int(row['clicks']), int(row['impressions'])))
    conn.commit()
    conn.close()

def upsert_gsc_devices(df):
    if df is None or df.empty: return
    conn = get_connection()
    cursor = conn.cursor()
    for _, row in df.iterrows():
        cursor.execute("""
        INSERT INTO gsc_devices (date, device, clicks, impressions)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT(date, device) DO UPDATE SET
            clicks=excluded.clicks,
            impressions=excluded.impressions
        """, (row['date'], str(row['device']), int(row['clicks']), int(row['impressions'])))
    conn.commit()
    conn.close()

def upsert_gsc_search_appearance(df):
    if df is None or df.empty: return
    conn = get_connection()
    cursor = conn.cursor()
    for _, row in df.iterrows():
        cursor.execute("""
        INSERT INTO gsc_search_appearance (date, appearance, clicks, impressions)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT(date, appearance) DO UPDATE SET
            clicks=excluded.clicks,
            impressions=excluded.impressions
        """, (row['date'], str(row['appearance']), int(row['clicks']), int(row['impressions'])))
    conn.commit()
    conn.close()

def upsert_ga4_gsc_landing_pages(df):
    if df is None or df.empty: return
    conn = get_connection()
    cursor = conn.cursor()
    for _, row in df.iterrows():
        try:
            cursor.execute("""
            INSERT INTO ga4_gsc_landing_pages (
                date, landing_page, clicks, impressions, ctr, position, 
                active_users, engaged_sessions, engagement_rate, avg_engagement_time, 
                event_count, key_events
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT(date, landing_page) DO UPDATE SET
                clicks=excluded.clicks,
                impressions=excluded.impressions,
                ctr=excluded.ctr,
                position=excluded.position,
                active_users=excluded.active_users,
                engaged_sessions=excluded.engaged_sessions,
                engagement_rate=excluded.engagement_rate,
                avg_engagement_time=excluded.avg_engagement_time,
                event_count=excluded.event_count,
                key_events=excluded.key_events
            """, (
                row['date'], str(row['landing_page']), 
                int(row['clicks']) if pd.notnull(row['clicks']) else 0, 
                int(row['impressions']) if pd.notnull(row['impressions']) else 0,
                float(row['ctr']) if pd.notnull(row['ctr']) else 0.0,
                float(row['position']) if pd.notnull(row['position']) else 0.0,
                int(row['active_users']) if pd.notnull(row['active_users']) else 0,
                int(row['engaged_sessions']) if pd.notnull(row['engaged_sessions']) else 0,
                float(row['engagement_rate']) if pd.notnull(row['engagement_rate']) else 0.0,
                float(row['avg_engagement_time']) if pd.notnull(row['avg_engagement_time']) else 0.0,
                int(row['event_count']) if pd.notnull(row['event_count']) else 0,
                int(row['key_events']) if pd.notnull(row['key_events']) else 0
            ))
        except Exception as e:
            print(f"Error inserting row: {e}")
    conn.commit()
    conn.close()

def get_advanced_gsc_data():
    conn = get_connection()
    from sqlalchemy import create_engine
    import pandas as pd
    from config.settings import SUPABASE_URI
    engine = create_engine(SUPABASE_URI.replace("postgresql://", "postgresql+psycopg2://"))
    
    try:
        pages = pd.read_sql_query("SELECT * FROM gsc_pages ORDER BY clicks DESC LIMIT 50", engine)
    except: pages = pd.DataFrame()
    
    try:
        countries = pd.read_sql_query("SELECT * FROM gsc_countries ORDER BY clicks DESC LIMIT 50", engine)
    except: countries = pd.DataFrame()
    
    try:
        devices = pd.read_sql_query("SELECT * FROM gsc_devices ORDER BY clicks DESC LIMIT 50", engine)
    except: devices = pd.DataFrame()
    
    try:
        appearance = pd.read_sql_query("SELECT * FROM gsc_search_appearance ORDER BY clicks DESC LIMIT 50", engine)
    except: appearance = pd.DataFrame()
    
    try:
        landing = pd.read_sql_query("SELECT * FROM ga4_gsc_landing_pages ORDER BY clicks DESC LIMIT 50", engine)
    except: landing = pd.DataFrame()
    
    return pages, countries, devices, appearance, landing
