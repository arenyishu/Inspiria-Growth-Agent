import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from database.db_manager import get_historical_data, fetch_ga4_advanced, fetch_gsc_advanced, save_ai_insights, get_latest_ai_insights, get_advanced_gsc_data
from engines.kpi_engine import calculate_percentage_change
from ai_layer.analyst import analyze_growth_data
import os
import plotly.express as px
import plotly.graph_objects as go

# --- PAGE CONFIG & CSS ---
st.set_page_config(page_title="Inspiria Growth Command Center", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    /* Theme-aware CSS using Streamlit's native variables */
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    
    .header-title { font-size: 28px; font-weight: bold; color: var(--text-color); margin: 0; }
    .header-subtitle { font-size: 14px; opacity: 0.7; color: var(--text-color); margin: 0; }
    
    .kpi-container { display: flex; gap: 20px; margin-bottom: 20px; }
    .kpi-card { background-color: var(--secondary-background-color); border: 1px solid rgba(128,128,128,0.2); border-radius: 8px; padding: 20px; flex: 1; box-shadow: 0 1px 2px rgba(0,0,0,0.05); display: flex; align-items: flex-start; gap: 15px; }
    .kpi-icon { width: 40px; height: 40px; background-color: rgba(26, 115, 232, 0.1); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 20px; }
    .kpi-content { flex: 1; }
    .kpi-title { font-size: 13px; opacity: 0.8; color: var(--text-color); font-weight: 600; margin: 0 0 5px 0; }
    .kpi-value { font-size: 28px; font-weight: bold; color: var(--text-color); margin: 0 0 10px 0; }
    
    .pill { display: inline-block; padding: 4px 8px; border-radius: 12px; font-size: 12px; font-weight: bold; }
    .pill.red { background-color: rgba(217, 48, 37, 0.15); color: #e57373; }
    .pill.green { background-color: rgba(19, 115, 51, 0.15); color: #81c784; }
    .vs-text { font-size: 12px; opacity: 0.6; color: var(--text-color); margin-left: 8px; }
    
    .alert-banner { background-color: rgba(250, 210, 119, 0.1); border: 1px solid #FAD277; border-radius: 8px; padding: 15px 20px; display: flex; align-items: center; gap: 15px; margin-bottom: 20px; }
    
    .chart-container { background-color: var(--secondary-background-color); border: 1px solid rgba(128,128,128,0.2); border-radius: 8px; padding: 20px; }
    
    .bottom-card { background-color: var(--secondary-background-color); border: 1px solid rgba(128,128,128,0.2); border-radius: 8px; padding: 20px; box-shadow: 0 1px 2px rgba(0,0,0,0.05); display: flex; align-items: flex-start; gap: 15px; height: 100%; }
</style>
""", unsafe_allow_html=True)


with st.sidebar:
    st.header("🎯 Set Monthly Targets")
    st.write("Used to calculate Scorecard attainment.")
    target_sessions = st.number_input("Target Sessions", value=15000)
    target_clicks = st.number_input("Target Organic Clicks", value=8000)
    target_reach = st.number_input("Target Social Reach", value=50000)
    target_q_leads = st.number_input("Target Qualified Leads", value=100)
    target_revenue = st.number_input("Target Pipeline Revenue ($)", value=50000)
    target_authority = st.number_input("Target Authority Score", value=60)
    
    st.markdown("---")
    st.header("⚙️ Admin Tools")
    if st.button("Force Sync / Rebuild Data", help="Generates fresh data from APIs."):
        import subprocess
        import sys
        
        # In Supabase, we don't wipe the DB. We just run the upserts!
        with st.spinner("Syncing data from APIs to Supabase..."):
            subprocess.run([sys.executable, "scripts/backfill_history.py"])
            subprocess.run([sys.executable, "scripts/backfill_semrush.py"])
            
        st.success("Data rebuilt! Refreshing...")
        st.rerun()

# --- FUNCTIONAL TABS ---
tab1, tab_seo, tab_ccc, tab2, tab3, tab4, tab5 = st.tabs(["Executive Scorecard", "SEO Deep Dive (New)", "Content Command Center", "Action Register", "Reports", "Data Sources", "Data Ingestion"])

with tab1:
    # --- HEADER & DATE FILTER ---
    col_head_left, col_head_right = st.columns([2, 1])

    with col_head_left:
        st.markdown('<p class="header-title">Executive Growth Dashboard</p>', unsafe_allow_html=True)
        st.markdown('<p class="header-subtitle">Performance vs Targets</p>', unsafe_allow_html=True)

    with col_head_right:
        period_options = {
            "Last 7 complete days": timedelta(days=7),
            "Last 14 days": timedelta(days=14),
            "Last 30 days": timedelta(days=30),
            "Last 3 months": relativedelta(months=3),
            "Last 6 months": relativedelta(months=6),
            "Last 1 year": relativedelta(years=1)
        }
        selected_period = st.selectbox("", list(period_options.keys()), label_visibility="collapsed")

    # --- DATE CALCULATIONS ---
    def get_latest_date():
        from database.db_manager import get_connection
        conn = get_connection()
        try:
            latest = pd.read_sql_query("SELECT MAX(date) as max_date FROM ga4_daily", conn).iloc[0]['max_date']
            return datetime.strptime(latest, '%Y-%m-%d') if latest else datetime.now()
        except:
            return datetime.now()
        finally:
            conn.close()

    anchor_date = get_latest_date()
    delta = period_options[selected_period]
    cur_end = anchor_date
    cur_start = anchor_date - delta + timedelta(days=1)
    prev_end = cur_start - timedelta(days=1)
    prev_start = prev_end - delta + timedelta(days=1)

    # Fetch Data
    ga4_cur, gsc_cur, social_cur, ga4_channels_cur, gsc_queries_cur, crm_cur, semrush_cur = get_historical_data(cur_start.strftime('%Y-%m-%d'), cur_end.strftime('%Y-%m-%d'))
    ga4_prev, gsc_prev, social_prev, ga4_channels_prev, gsc_queries_prev, crm_prev, semrush_prev = get_historical_data(prev_start.strftime('%Y-%m-%d'), prev_end.strftime('%Y-%m-%d'))

    # Calculate KPIs
    def get_totals(df, metric):
        return df[metric].sum() if not df.empty else 0

    c_clicks = get_totals(gsc_cur, 'clicks')
    p_clicks = get_totals(gsc_prev, 'clicks')
    chg_clicks = calculate_percentage_change(c_clicks, p_clicks)

    c_imp = get_totals(gsc_cur, 'impressions')
    p_imp = get_totals(gsc_prev, 'impressions')
    chg_imp = calculate_percentage_change(c_imp, p_imp)

    c_sess = get_totals(ga4_cur, 'sessions')
    p_sess = get_totals(ga4_prev, 'sessions')
    chg_sess = calculate_percentage_change(c_sess, p_sess)

    c_users = get_totals(ga4_cur, 'active_users')
    p_users = get_totals(ga4_prev, 'active_users')
    chg_users = calculate_percentage_change(c_users, p_users)

    c_pv = get_totals(ga4_cur, 'pageviews')
    p_pv = get_totals(ga4_prev, 'pageviews')
    chg_pv = calculate_percentage_change(c_pv, p_pv)

    # Calculate Social Sessions directly from GA4 instead of manual uploads
    c_reach = ga4_channels_cur[ga4_channels_cur['channel'].str.contains('Social', case=False, na=False)]['sessions'].sum() if not ga4_channels_cur.empty else 0
    p_reach = ga4_channels_prev[ga4_channels_prev['channel'].str.contains('Social', case=False, na=False)]['sessions'].sum() if not ga4_channels_prev.empty else 0
    chg_reach = calculate_percentage_change(c_reach, p_reach)

    c_q_leads = len(crm_cur[crm_cur['qualified'].str.lower() == 'yes']) if not crm_cur.empty and 'qualified' in crm_cur.columns else 0
    p_q_leads = len(crm_prev[crm_prev['qualified'].str.lower() == 'yes']) if not crm_prev.empty and 'qualified' in crm_prev.columns else 0
    chg_q_leads = calculate_percentage_change(c_q_leads, p_q_leads)

    c_rev = crm_cur['revenue'].sum() if not crm_cur.empty and 'revenue' in crm_cur.columns else 0
    p_rev = crm_prev['revenue'].sum() if not crm_prev.empty and 'revenue' in crm_prev.columns else 0
    chg_rev = calculate_percentage_change(c_rev, p_rev)

    # SEMrush Metrics (take the latest day's value for Authority)
    c_auth = semrush_cur.iloc[-1]['authority_score'] if not semrush_cur.empty and 'authority_score' in semrush_cur.columns else 0
    p_auth = semrush_prev.iloc[-1]['authority_score'] if not semrush_prev.empty and 'authority_score' in semrush_prev.columns else 0
    chg_auth = calculate_percentage_change(c_auth, p_auth)

    # Scale targets
    days = (cur_end - cur_start).days + 1
    t_sess = target_sessions * (days / 30.0)
    t_clicks = target_clicks * (days / 30.0)
    t_reach = target_reach * (days / 30.0)
    t_q_leads = target_q_leads * (days / 30.0)
    t_rev = target_revenue * (days / 30.0)
    t_auth = target_authority # Authority is absolute, not scaled by days

    def get_status(c, t):
        if t == 0: return "⚪ N/A"
        att = c/t
        if att >= 0.95: return "🟢 On Track"
        elif att >= 0.80: return "🟡 Watch"
        else: return "🔴 At Risk"

    def format_row(name, c, p, chg, t, prefix=""):
        att = f"{(c/t)*100:.1f}%" if t > 0 else "N/A"
        color = "lightgreen" if chg >= 0 else "salmon"
        return f"""<tr>
<td style="padding: 10px; border-bottom: 1px solid rgba(128,128,128,0.2); font-weight: bold;">{name}</td>
<td style="padding: 10px; border-bottom: 1px solid rgba(128,128,128,0.2);">{prefix}{int(c):,}</td>
<td style="padding: 10px; border-bottom: 1px solid rgba(128,128,128,0.2);">{prefix}{int(p):,}</td>
<td style="padding: 10px; border-bottom: 1px solid rgba(128,128,128,0.2); color: {color};">{chg:+.1f}%</td>
<td style="padding: 10px; border-bottom: 1px solid rgba(128,128,128,0.2);">{prefix}{int(t):,}</td>
<td style="padding: 10px; border-bottom: 1px solid rgba(128,128,128,0.2);">{att}</td>
<td style="padding: 10px; border-bottom: 1px solid rgba(128,128,128,0.2);">{get_status(c, t)}</td>
</tr>"""

    # --- EXECUTIVE SCORECARD ---
    st.markdown(f"""
<div style="background: var(--secondary-background-color); border-radius: 8px; padding: 15px; margin-bottom: 20px;">
<table style="width:100%; border-collapse: collapse; font-family: sans-serif; color: var(--text-color); font-size: 14px;">
<tr style="background: rgba(128,128,128,0.1); text-align: left;">
<th style="padding: 10px; border-bottom: 1px solid rgba(128,128,128,0.2);">Metric</th>
<th style="padding: 10px; border-bottom: 1px solid rgba(128,128,128,0.2);">Current</th>
<th style="padding: 10px; border-bottom: 1px solid rgba(128,128,128,0.2);">Previous</th>
<th style="padding: 10px; border-bottom: 1px solid rgba(128,128,128,0.2);">MoM %</th>
<th style="padding: 10px; border-bottom: 1px solid rgba(128,128,128,0.2);">Target ({days}d)</th>
<th style="padding: 10px; border-bottom: 1px solid rgba(128,128,128,0.2);">Attainment</th>
<th style="padding: 10px; border-bottom: 1px solid rgba(128,128,128,0.2);">Status</th>
</tr>
{format_row('Authority Score (SEMrush)', c_auth, p_auth, chg_auth, t_auth)}
{format_row('Pipeline Revenue', c_rev, p_rev, chg_rev, t_rev, '$')}
{format_row('Qualified Leads', c_q_leads, p_q_leads, chg_q_leads, t_q_leads)}
{format_row('Website Sessions', c_sess, p_sess, chg_sess, t_sess)}
{format_row('Organic Clicks', c_clicks, p_clicks, chg_clicks, t_clicks)}
{format_row('Social Media Sessions', c_reach, p_reach, chg_reach, t_reach)}
</table>
</div>
    """, unsafe_allow_html=True)

    # --- ALERT BANNER ---
    if chg_clicks <= -20 or chg_imp <= -20:
        st.markdown("""
        <div class="alert-banner">
            <span style="font-size: 24px;">⚠️</span>
            <div>
                <div style="font-weight: bold; font-size: 16px; color: var(--text-color);">Search visibility needs attention</div>
                <div style="font-size: 14px; opacity: 0.8; color: var(--text-color);">Clicks and impressions declined significantly by more than 20%.</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # --- CHARTS ---
    col_ch1, col_ch2 = st.columns(2)

    with col_ch1:
        st.markdown("""
        <div class="chart-container">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                <div>
                    <h3 style="margin: 0; font-size: 18px; color: var(--text-color);">Website performance</h3>
                    <p style="margin: 0; font-size: 12px; opacity: 0.7; color: var(--text-color);">Sessions over time (with 7-day forecast)</p>
                </div>
            </div>
        """, unsafe_allow_html=True)
        if not ga4_cur.empty:
            chart_df = ga4_cur.copy()
            chart_df['type'] = 'Actual'
            
            # Simple 7-day forecast using the recent average
            if len(chart_df) >= 7:
                avg_trend = chart_df['sessions'].tail(7).mean()
                last_date = pd.to_datetime(chart_df['date'].max())
                forecast_dates = [(last_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(1, 8)]
                forecast_df = pd.DataFrame({'date': forecast_dates, 'sessions': [avg_trend]*7, 'type': 'Forecast'})
                chart_df = pd.concat([chart_df, forecast_df])
            
            fig_area = px.area(chart_df, x="date", y="sessions", color="type", 
                               color_discrete_map={'Actual': '#42a5f5', 'Forecast': '#ffa726'})
            fig_area.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=300, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#80868B'))
            fig_area.update_layout(legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01))
            st.plotly_chart(fig_area, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_ch2:
        st.markdown("""
        <div class="chart-container">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                <div>
                    <h3 style="margin: 0; font-size: 18px; color: var(--text-color);">Search performance</h3>
                    <p style="margin: 0; font-size: 12px; opacity: 0.7; color: var(--text-color);">Impressions over time</p>
                </div>
            </div>
        """, unsafe_allow_html=True)
        if not gsc_cur.empty:
            chart_df_gsc = gsc_cur.set_index('date')[['impressions']]
            st.area_chart(chart_df_gsc)
        st.markdown("</div>", unsafe_allow_html=True)

    # --- MARKETING FUNNEL ---
    st.markdown("<br><h2 style='font-size: 20px; color: var(--text-color); margin-bottom: 20px;'>The Marketing Funnel</h2>", unsafe_allow_html=True)
    funnel_data = dict(
        number=[c_reach + c_imp, c_clicks, c_sess, c_users],
        stage=["Top of Funnel (Awareness: Social Sessions + Search Impressions)", "Middle of Funnel (Interest: Search Clicks)", "Website Traffic (GA4 Sessions)", "Bottom of Funnel (GA4 Active Users)"]
    )
    if funnel_data['number'][0] > 0:
        fig_funnel = px.funnel(funnel_data, x='number', y='stage')
        fig_funnel.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=350, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#80868B'))
        fig_funnel.update_traces(marker=dict(color=['#5c6bc0', '#42a5f5', '#26c6da', '#66bb6a']))
        st.plotly_chart(fig_funnel, use_container_width=True)
    else:
        st.info("Upload social data or ensure search data exists to view the funnel.")

    # --- SEMRUSH SITE AUDIT ---
    st.markdown("<br><h2 style='font-size: 20px; color: var(--text-color); margin-bottom: 20px;'>Technical SEO (SEMrush Audit)</h2>", unsafe_allow_html=True)
    try:
        from database.db_manager import get_connection
        conn = get_connection()
        import pandas as pd
        audit_df = pd.read_sql_query("SELECT * FROM semrush_site_audit", conn)
        conn.close()
        
        if not audit_df.empty:
            total_pages = len(audit_df)
            slow_pages = len(audit_df[audit_df['page_html_load_time_sec'] > 2.0])
            orphan_pages = len(audit_df[audit_df['incoming_internal_links'] == 0])
            
            st.markdown(f"""
            <div class="kpi-container">
                <div class="kpi-card">
                    <div class="kpi-value">{total_pages:,}</div>
                    <div class="kpi-label">Total Pages Crawled</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-value" style="color: #ef5350;">{slow_pages:,}</div>
                    <div class="kpi-label">Slow Pages (> 2s Load)</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-value" style="color: #ff9800;">{orphan_pages:,}</div>
                    <div class="kpi-label">Orphan Pages (0 Internal Links)</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.caption("View the full breakdown and cross-reference this with your traffic on the 'Content Command Center' tab.")
        else:
            st.info("No SEMrush data available.")
    except Exception as e:
        st.info("No SEMrush data available.")

    # --- ADVANCED ANALYTICS ---
    st.markdown("<br><h2 style='font-size: 20px; color: var(--text-color); margin-bottom: 20px;'>Deep Analytics</h2>", unsafe_allow_html=True)
    
    col_adv1, col_adv2 = st.columns([1, 2])
    
    with col_adv1:
        st.markdown("""
        <div class="chart-container">
            <h3 style="margin: 0; font-size: 18px; color: var(--text-color);">Traffic Channels</h3>
            <p style="margin: 0 0 15px 0; font-size: 12px; opacity: 0.7; color: var(--text-color);">Sessions by source</p>
        """, unsafe_allow_html=True)
        if not ga4_channels_cur.empty:
            ch_grouped = ga4_channels_cur.groupby('channel')['sessions'].sum().reset_index()
            fig = px.pie(ch_grouped, values='sessions', names='channel', hole=0.6, 
                         color_discrete_sequence=px.colors.qualitative.Pastel)
            fig.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=250, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#80868B'))
            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_adv2:
        st.markdown("""
        <div class="chart-container" style="height: 100%;">
            <h3 style="margin: 0; font-size: 18px; color: var(--text-color);">Top Search Queries</h3>
            <p style="margin: 0 0 15px 0; font-size: 12px; opacity: 0.7; color: var(--text-color);">What users typed into Google</p>
        """, unsafe_allow_html=True)
        if not gsc_queries_cur.empty:
            q_grouped = gsc_queries_cur.groupby('query')['clicks'].sum().reset_index().sort_values(by='clicks', ascending=False)
            st.dataframe(q_grouped.head(7), use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)

    
    # --- ADVANCED SEO DEEP DIVE ---
    st.markdown("<br><h2 style='font-size: 20px; color: var(--text-color); margin-bottom: 20px;'>Advanced SEO & Traffic Deep Dive</h2>", unsafe_allow_html=True)
    
    pages_df, countries_df, devices_df, appearance_df, landing_df = get_advanced_gsc_data()
    
    adv_tab1, adv_tab2, adv_tab3, adv_tab4, adv_tab5 = st.tabs([
        "Top Landing Pages (GA4+GSC)", "Top Pages (GSC)", "Top Countries", "Top Devices", "Search Appearance"
    ])
    
    with adv_tab1:
        if not landing_df.empty:
            st.dataframe(landing_df.drop(columns=['date'], errors='ignore'), use_container_width=True, hide_index=True)
        else:
            st.info("No Landing Page data available.")
            
    with adv_tab2:
        if not pages_df.empty:
            st.dataframe(pages_df.drop(columns=['date'], errors='ignore'), use_container_width=True, hide_index=True)
        else:
            st.info("No Pages data available.")
            
    with adv_tab3:
        if not countries_df.empty:
            st.dataframe(countries_df.drop(columns=['date'], errors='ignore'), use_container_width=True, hide_index=True)
        else:
            st.info("No Countries data available.")
            
    with adv_tab4:
        if not devices_df.empty:
            st.dataframe(devices_df.drop(columns=['date'], errors='ignore'), use_container_width=True, hide_index=True)
        else:
            st.info("No Devices data available.")
            
    with adv_tab5:
        if not appearance_df.empty:
            st.dataframe(appearance_df.drop(columns=['date'], errors='ignore'), use_container_width=True, hide_index=True)
        else:
            st.info("No Search Appearance data available.")

    # --- AI ANALYST & RECOMMENDATIONS ---
    st.markdown("<br>", unsafe_allow_html=True)

    if "ai_results" not in st.session_state:
        st.session_state.ai_results = get_latest_ai_insights()

    with st.container():
        c_banner_l, c_banner_r = st.columns([3, 1])
        with c_banner_l:
            st.markdown("""
            <div style="display: flex; align-items: center; gap: 15px; margin-top: 10px;">
                <div style="background: rgba(26, 115, 232, 0.1); padding: 10px; border-radius: 8px; font-size: 24px;">✨</div>
                <div>
                    <h3 style="margin:0; font-size: 16px; color: var(--text-color);">AI Analyst</h3>
                    <p style="margin:0; font-size: 13px; opacity: 0.7; color: var(--text-color);">Click generate to scan the selected date range and detect anomalies.</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
        with c_banner_r:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("✨ Generate AI insights", type="primary", use_container_width=True):
                with st.spinner("Analyzing..."):
                    top_queries = {}
                    if not gsc_queries_cur.empty:
                        top_queries = gsc_queries_cur.groupby('query')['clicks'].sum().nlargest(5).to_dict()
                    
                    top_channels = {}
                    if not ga4_channels_cur.empty:
                        top_channels = ga4_channels_cur.groupby('channel')['sessions'].sum().nlargest(5).to_dict()

                    evidence = {
                        "marketing_funnel": {
                            "top_of_funnel_awareness": int(c_reach + c_imp),
                            "middle_of_funnel_interest": int(c_clicks),
                            "website_traffic_sessions": int(c_sess),
                            "bottom_of_funnel_active_users": int(c_users)
                        },
                        "ga4_performance": {
                            "sessions": {"current": int(c_sess), "previous": int(p_sess), "change_pct": round(chg_sess, 2)},
                            "top_channels_by_sessions": top_channels
                        },
                        "gsc_performance": {
                            "clicks": {"current": int(c_clicks), "previous": int(p_clicks), "change_pct": round(chg_clicks, 2)},
                            "impressions": {"current": int(c_imp), "previous": int(p_imp), "change_pct": round(chg_imp, 2)},
                            "top_search_queries_driving_traffic": top_queries
                        },
                        "social_media_performance": {
                            "reach": {"current": int(c_reach), "previous": int(p_reach), "change_pct": round(chg_reach, 2)}
                        },
                        "semrush_authority": {
                            "authority_score": {"current": int(c_auth), "previous": int(p_auth), "change_pct": round(chg_auth, 2)}
                        }
                    }
                    st.session_state.ai_results = analyze_growth_data(evidence)
                    if st.session_state.ai_results:
                        save_ai_insights(st.session_state.ai_results)
                        
                        # Auto-assign tasks to the Action Register
                        from database.db_manager import add_action_task
                        for action in st.session_state.ai_results.get("recommended_actions", []):
                            add_action_task(f"[AI] {action}", "High")

    if st.session_state.ai_results:
        st.success("Analysis Complete!")
        ai = st.session_state.ai_results
        st.write(f"**Executive Summary:** {ai.get('summary', '')}")
        
        st.markdown("### Recommended investigations")
        st.caption("Suggested next steps, not a diagnosis.")
        
        r1, r2, r3 = st.columns(3)
        actions = ai.get("recommended_actions", ["Review declining pages", "Check query visibility", "Validate conversion tracking"])
        while len(actions) < 3:
            actions.append("Continue monitoring trends.")
            
        with r1:
            st.markdown(f'<div class="bottom-card"><div style="background: rgba(26, 115, 232, 0.1); padding: 8px; border-radius: 4px;">📄</div><div><div style="font-weight: 600; font-size: 14px; color: var(--text-color);">Action 1</div><div style="font-size: 12px; opacity: 0.7; color: var(--text-color);">{actions[0]}</div></div></div>', unsafe_allow_html=True)
        with r2:
            st.markdown(f'<div class="bottom-card"><div style="background: rgba(26, 115, 232, 0.1); padding: 8px; border-radius: 4px;">🔍</div><div><div style="font-weight: 600; font-size: 14px; color: var(--text-color);">Action 2</div><div style="font-size: 12px; opacity: 0.7; color: var(--text-color);">{actions[1]}</div></div></div>', unsafe_allow_html=True)
        with r3:
            st.markdown(f'<div class="bottom-card"><div style="background: rgba(26, 115, 232, 0.1); padding: 8px; border-radius: 4px;">📊</div><div><div style="font-weight: 600; font-size: 14px; color: var(--text-color);">Action 3</div><div style="font-size: 12px; opacity: 0.7; color: var(--text-color);">{actions[2]}</div></div></div>', unsafe_allow_html=True)
    else:
        st.markdown("<br><h3 style='font-size: 16px; color: var(--text-color);'>Recommended investigations</h3><p style='font-size: 12px; opacity: 0.7; color: var(--text-color);'>Suggested next steps, not a diagnosis.</p>", unsafe_allow_html=True)
        r1, r2, r3 = st.columns(3)
        with r1:
            st.markdown('<div class="bottom-card"><div style="background: rgba(26, 115, 232, 0.1); padding: 8px; border-radius: 4px;">📄</div><div><div style="font-weight: 600; font-size: 14px; color: var(--text-color);">Review declining pages</div><div style="font-size: 12px; opacity: 0.7; color: var(--text-color);">Identify top pages with the largest drops in clicks and impressions.</div></div></div>', unsafe_allow_html=True)
        with r2:
            st.markdown('<div class="bottom-card"><div style="background: rgba(26, 115, 232, 0.1); padding: 8px; border-radius: 4px;">🔍</div><div><div style="font-weight: 600; font-size: 14px; color: var(--text-color);">Check query visibility</div><div style="font-size: 12px; opacity: 0.7; color: var(--text-color);">Review key queries with declining impressions and position changes.</div></div></div>', unsafe_allow_html=True)
        with r3:
            st.markdown('<div class="bottom-card"><div style="background: rgba(26, 115, 232, 0.1); padding: 8px; border-radius: 4px;">📊</div><div><div style="font-weight: 600; font-size: 14px; color: var(--text-color);">Validate tracking</div><div style="font-size: 12px; opacity: 0.7; color: var(--text-color);">Confirm tracking is working as expected and compare with other data sources.</div></div></div>', unsafe_allow_html=True)


with tab_seo:
    st.markdown("### SEO Deep Dive & User Journey")
    st.markdown("Powered by Multi-Dimensional advanced API extractions.")
    
    # Load Advanced Data
    ga4_adv = fetch_ga4_advanced()
    gsc_adv = fetch_gsc_advanced()
    
    if not gsc_adv.empty and not ga4_adv.empty:
        # 1. FUNNEL CHART
        st.markdown("#### 1. The Growth Funnel (Impressions to Conversions)")
        total_imp = gsc_adv['impressions'].sum()
        total_clicks = gsc_adv['clicks'].sum()
        total_sessions = ga4_adv['sessions'].sum()
        total_conv = ga4_adv['conversions'].sum()
        
        fig_funnel = go.Figure(go.Funnel(
            y=["GSC Impressions", "GSC Clicks", "GA4 Sessions", "GA4 Conversions"],
            x=[total_imp, total_clicks, total_sessions, total_conv],
            textposition="inside",
            textinfo="value+percent initial",
            marker={"color": ["#4285F4", "#34A853", "#FBBC05", "#EA4335"]}
        ))
        fig_funnel.update_layout(margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig_funnel, use_container_width=True)
        
        # 2. STRIKING DISTANCE
        st.markdown("#### 2. 'Striking Distance' Keywords (Positions 11-20)")
        striking_df = gsc_adv[(gsc_adv['position'] >= 11) & (gsc_adv['position'] <= 25)].copy()
        if not striking_df.empty:
            # Group by query to aggregate
            striking_agg = striking_df.groupby('query').agg({'impressions':'sum', 'clicks':'sum', 'position':'mean'}).reset_index()
            # Top 50 by impressions
            striking_agg = striking_agg.sort_values('impressions', ascending=False).head(50)
            
            fig_scatter = px.scatter(
                striking_agg, x="position", y="impressions", size="impressions", color="clicks",
                hover_name="query", size_max=40,
                color_continuous_scale="Viridis",
                title="Keywords on Page 2 or 3 with High Impressions (Need On-Page Optimization)"
            )
            # Invert X axis so rank 11 is on the left
            fig_scatter.update_xaxes(autorange="reversed")
            st.plotly_chart(fig_scatter, use_container_width=True)
        else:
            st.info("No striking distance keywords found (Positions 11-25).")

        # 3. TRAFFIC COMPOSITION
        st.markdown("#### 3. Traffic Composition")
        colA, colB = st.columns(2)
        with colA:
            # Device Donut
            device_agg = ga4_adv.groupby('device')['sessions'].sum().reset_index()
            fig_donut = px.pie(device_agg, values='sessions', names='device', hole=0.5, title="Sessions by Device")
            st.plotly_chart(fig_donut, use_container_width=True)
        with colB:
            # Channel Bar
            channel_agg = ga4_adv.groupby('source')['sessions'].sum().reset_index().sort_values('sessions', ascending=False).head(10)
            fig_bar = px.bar(channel_agg, x='source', y='sessions', title="Top 10 Sources by Sessions", color='sessions', color_continuous_scale="Blues")
            st.plotly_chart(fig_bar, use_container_width=True)
            
        # 4. RAW DATA GRID WITH HIGHLIGHTS
        st.markdown("#### 4. Actionable Data Grids")
        st.markdown("**Content Decay Watchlist (Pages losing traffic):** *(Requires AI Phase 2 logic to fully calculate decay, showing raw top pages for now)*")
        # Just show a stylized dataframe for now
        page_agg = gsc_adv.groupby('landing_page').agg({'clicks':'sum', 'impressions':'sum', 'position':'mean'}).reset_index().sort_values('clicks', ascending=False).head(20)
        st.dataframe(page_agg.style.background_gradient(subset=['clicks'], cmap='Greens').background_gradient(subset=['impressions'], cmap='Blues'))
        
    else:
        st.info("Advanced data is still syncing from Google. Please wait a few minutes and refresh.")



with tab_ccc:
    st.header("Content Command Center (Phase 3)")
    st.write("This unified data lake merges your real Google Search Console traffic with your SEMrush Site Audit metrics to expose hidden technical bottlenecks.")
    
    try:
        from database.db_manager import get_connection
        import pandas as pd
        
        conn = get_connection()
        
        with st.spinner("Merging GSC Traffic with SEMrush Technical Data..."):
            query = """
                SELECT 
                    a.page_url,
                    a.page_title,
                    COALESCE(SUM(g.clicks), 0) as total_clicks,
                    COALESCE(SUM(g.impressions), 0) as total_impressions,
                    a.incoming_internal_links,
                    a.page_html_load_time_sec as load_time,
                    a.http_status_code
                FROM semrush_site_audit a
                LEFT JOIN gsc_advanced_report g ON a.page_url = g.landing_page
                GROUP BY a.page_url, a.page_title, a.incoming_internal_links, a.page_html_load_time_sec, a.http_status_code
                ORDER BY total_impressions DESC
                LIMIT 500
            """
            merged_df = pd.read_sql_query(query, conn)
            conn.close()
            
            if not merged_df.empty:
                st.subheader("Unified Data Lake (Top 500 Pages by Search Impressions)")
                st.dataframe(merged_df, use_container_width=True)
                
                # Insight 1: High Impressions, Zero Internal Links (Orphan Pages)
                st.divider()
                st.subheader("🚨 Critical Bottleneck: High Traffic Orphan Pages")
                st.write("These pages are ranking on Google and getting thousands of impressions, but you have 0 internal links pointing to them on your own website. Adding internal links to these pages will boost their authority massively.")
                orphan_df = merged_df[(merged_df['incoming_internal_links'] == 0) & (merged_df['total_impressions'] > 100)]
                if not orphan_df.empty:
                    st.dataframe(orphan_df[['page_url', 'total_impressions', 'total_clicks', 'incoming_internal_links']], use_container_width=True)
                else:
                    st.success("No high-traffic orphan pages found! Great job.")
                    
                # Insight 2: High Clicks, Slow Load Time
                st.divider()
                st.subheader("🐌 Speed Warning: Slow Loading Traffic Engines")
                st.write("These pages generate the most clicks for your business, but take longer than 2.0 seconds to load. Speeding these up will instantly improve conversion rates.")
                slow_df = merged_df[(merged_df['load_time'] > 2.0) & (merged_df['total_clicks'] > 50)]
                if not slow_df.empty:
                    st.dataframe(slow_df[['page_url', 'total_clicks', 'load_time']], use_container_width=True)
                else:
                    st.success("Your top traffic pages load fast!")
                    
            else:
                st.info("No SEMrush data found.")
    except Exception as e:
        st.error(f"Error loading Content Command Center: {e}")

with tab2:
    st.header("Action Register (AI SEO Tagging)")
    st.write("Track strategic tasks and automatically tag your massive keyword lists using Gemini AI.")
    
    # AI Tagging Section
    st.markdown("### Phase 2: AI Keyword Analysis")
    st.markdown("You have thousands of raw keywords in your database. Click the button below to have Gemini automatically tag them with Search Intent and Topic Clusters in batches.")
    
    if st.button("▶ Run AI Tagging Batch (1000 Keywords)"):
        with st.spinner("Gemini AI is analyzing keywords... (this takes ~30-60 seconds to avoid rate limits)"):
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
            from ai_layer.keyword_tagger import tag_keywords_batch
            
            success = tag_keywords_batch()
            if success:
                st.success("Batch successfully tagged and saved to the database!")
                # small delay so user sees success before rerun
                import time
                time.sleep(1)
                st.rerun()
            else:
                st.error("Something went wrong during tagging or rate limit was hit. Check logs.")
                
    st.divider()
    st.subheader("Currently Tagged Keywords")
    
    try:
        from database.db_manager import get_tagged_keywords
        tagged_df = get_tagged_keywords()
        if not tagged_df.empty:
            st.metric("Total Tagged Keywords", len(tagged_df))
            st.dataframe(tagged_df, use_container_width=True)
            
            # Show a cool pie chart of intent
            import plotly.express as px
            intent_counts = tagged_df['intent'].value_counts().reset_index()
            intent_counts.columns = ['Intent', 'Count']
            fig = px.pie(intent_counts, values='Count', names='Intent', title='Search Intent Distribution', hole=0.4)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No keywords have been tagged yet. Click the button above to start!")
    except Exception as e:
        st.error(f"Could not load tags: {e}")
        
    st.divider()
    
    # Original Action Tracking logic
    col_a1, col_a2 = st.columns([3, 1])
    with col_a1:
        new_task = st.text_input("New Task", placeholder="e.g., Improve CTR on Pricing page", label_visibility="collapsed")
    with col_a2:
        new_priority = st.selectbox("Priority", ["High", "Medium", "Low"], label_visibility="collapsed")
    
    if st.button("Add Task"):
        if new_task:
            from database.db_manager import add_action_task
            add_action_task(new_task, new_priority)
            st.rerun()
            
    from database.db_manager import get_action_tasks
    tasks_df = get_action_tasks()
    if not tasks_df.empty:
        for idx, row in tasks_df.iterrows():
            col1, col2, col3 = st.columns([1, 4, 1])
            with col1:
                st.write(f"**[{row['priority']}]**")
            with col2:
                st.write(row['task_name'])
            with col3:
                if row['status'] != 'Done':
                    if st.button("Complete", key=f"complete_{row['task_id']}"):
                        from database.db_manager import complete_action_task
                        complete_action_task(row['task_id'])
                        st.rerun()
                else:
                    st.write("✅ Done")
    else:
        st.info("No tasks yet. Add a task manually above.")

with tab3:
    st.header("Reports Module (Weekly Review)")
    st.write("Click 'Generate AI insights' on the Executive Scorecard tab to generate your automated Weekly Review here.")
    if st.session_state.ai_results:
        ai = st.session_state.ai_results
        st.success("Weekly Review Generated successfully!")
        st.write(f"**Executive Summary:** {ai.get('summary', '')}")
        st.write("### Recommended Action Items")
        for action in ai.get("recommended_actions", []):
            st.write(f"- {action}")
    else:
        st.info("No report generated yet.")
    
with tab4:
    st.header("Raw Data Sources")
    st.write("View the exact, raw data pulled from your connected sources.")
    
    st.subheader("Google Analytics 4 (Website Traffic)")
    st.dataframe(ga4_cur)
    
    st.subheader("Google Search Console (Organic Search)")
    st.dataframe(gsc_cur)
    
    st.subheader("Social Media (Automated via GA4)")
    social_traffic = ga4_channels_cur[ga4_channels_cur['channel'].str.contains('Social', case=False, na=False)] if not ga4_channels_cur.empty else None
    if social_traffic is not None and not social_traffic.empty:
        st.dataframe(social_traffic)
    else:
        st.info("No Organic Social traffic recorded in GA4 for this period.")

    st.subheader("SEMrush (Technical Site Audit)")
    try:
        from database.db_manager import get_connection
        conn = get_connection()
        import pandas as pd
        audit_raw_df = pd.read_sql_query("SELECT * FROM semrush_site_audit", conn)
        conn.close()
        if not audit_raw_df.empty:
            st.write(f"Showing all {len(audit_raw_df):,} crawled URLs.")
            st.dataframe(audit_raw_df)
        else:
            st.info("No SEMrush Site Audit data found in database.")
    except Exception as e:
        st.info("No SEMrush data available for this period.")


def safe_read_csv(file_obj):
    import pandas as pd
    import io
    content = file_obj.getvalue().decode('utf-8', errors='replace')
    lines = content.split('\n')
    
    start_idx = 0
    # Scan first 25 lines for typical header keywords to skip Google's junk metadata
    for i, line in enumerate(lines[:25]):
        lower_line = line.lower()
        if 'date' in lower_line or 'clicks' in lower_line or 'sessions' in lower_line or 'total followers' in lower_line or 'conversion_id' in lower_line or 'authority' in lower_line:
            start_idx = i
            break
            
    df = pd.read_csv(io.StringIO('\n'.join(lines[start_idx:])))
    # Standardize column names
    df.columns = [str(c).strip().lower().replace(' ', '_') for c in df.columns]
    return df

with tab5:
    st.header("Universal Data Ingestion Hub")
    st.write("Upload your exported CSV data files to securely push them to the Supabase Data Warehouse. The system will preview your data before saving.")
    
    import pandas as pd
    from sqlalchemy import create_engine
    import os
    
    # We use a direct engine for pandas to_sql
    try:
        if "SUPABASE_URI" in st.secrets:
            db_uri = st.secrets["SUPABASE_URI"]
        else:
            db_uri = os.getenv("SUPABASE_URI", "")
            
        engine = create_engine(db_uri.replace("postgresql://", "postgresql+psycopg2://"))
    except Exception as e:
        engine = None
        st.error("Could not connect to database engine.")

    # 1. SEMrush Site Audit
    with st.expander("🛠️ SEMrush (Technical Site Audit)"):
        st.write("Upload your SEMrush Site Audit export (updates the Content Command Center).")
        up_audit = st.file_uploader("Upload Site Audit CSV", type="csv", key="up_audit")
        if up_audit:
            try:
                df_audit = safe_read_csv(up_audit)
                st.write("**Data Preview:**")
                st.dataframe(df_audit.head())
                if st.button("Submit to Database", key="btn_audit"):
                    with st.spinner("Saving to database..."):
                        if engine:
                            df_audit.to_sql('semrush_site_audit', engine, if_exists='replace', index=False)
                            st.success(f"Successfully saved {len(df_audit)} rows!")
            except Exception as e:
                st.error(f"Error reading file: {e}")

    # 2. SEMrush Domain Authority
    with st.expander("📈 SEMrush (Domain Authority)"):
        st.write("Upload your SEMrush Domain Overview (columns: date, authority_score, total_backlinks, organic_keywords).")
        up_sem = st.file_uploader("Upload Domain CSV", type="csv", key="up_sem")
        if up_sem:
            try:
                df_sem = safe_read_csv(up_sem)
                st.write("**Data Preview:**")
                st.dataframe(df_sem.head())
                if st.button("Submit to Database", key="btn_sem"):
                    with st.spinner("Saving to database..."):
                        if engine:
                            df_sem.to_sql('semrush_daily', engine, if_exists='append', index=False)
                            st.success(f"Successfully saved {len(df_sem)} rows!")
            except Exception as e:
                st.error(f"Error: {e}")

    # 3. Social Media Native
    with st.expander("📱 Social Media (Native Metrics)"):
        st.write("Upload native social metrics (columns: date, reach, impressions, followers, engagement).")
        up_soc = st.file_uploader("Upload Social CSV", type="csv", key="up_soc")
        if up_soc:
            try:
                df_soc = safe_read_csv(up_soc)
                st.write("**Data Preview:**")
                st.dataframe(df_soc.head())
                if st.button("Submit to Database", key="btn_soc"):
                    with st.spinner("Saving to database..."):
                        if engine:
                            df_soc.to_sql('social_daily', engine, if_exists='append', index=False)
                            st.success(f"Successfully saved {len(df_soc)} rows!")
            except Exception as e:
                st.error(f"Error: {e}")

    # 4. CRM Pipeline
    with st.expander("💼 CRM Conversions (Pipeline)"):
        st.write("Upload your sales pipeline (columns: date, source, total_leads, qualified_leads, enrolled_students, revenue).")
        up_crm = st.file_uploader("Upload CRM CSV", type="csv", key="up_crm")
        if up_crm:
            try:
                df_crm = safe_read_csv(up_crm)
                st.write("**Data Preview:**")
                st.dataframe(df_crm.head())
                if st.button("Submit to Database", key="btn_crm"):
                    with st.spinner("Saving to database..."):
                        if engine:
                            df_crm.to_sql('crm_pipeline', engine, if_exists='append', index=False)
                            st.success(f"Successfully saved {len(df_crm)} rows!")
            except Exception as e:
                st.error(f"Error: {e}")

    # 5. GA4 Fallback
    with st.expander("📊 Google Analytics 4 (Fallback)"):
        st.write("Upload your GA4 export (columns: date, sessions, totalUsers, activeUsers, screenPageViews). Note: This is usually automatically fetched via API.")
        up_ga4 = st.file_uploader("Upload GA4 CSV", type="csv", key="up_ga4")
        if up_ga4:
            try:
                df_ga4 = safe_read_csv(up_ga4)
                st.write("**Data Preview:**")
                st.dataframe(df_ga4.head())
                if st.button("Submit to Database", key="btn_ga4"):
                    with st.spinner("Saving to database..."):
                        if engine:
                            df_ga4.to_sql('ga4_daily', engine, if_exists='append', index=False)
                            st.success(f"Successfully saved {len(df_ga4)} rows!")
            except Exception as e:
                st.error(f"Error: {e}")

    # 6. GSC Fallback
    with st.expander("🔍 Google Search Console (Fallback)"):
        st.write("Upload your GSC export (columns: date, query, landing_page, country, device, clicks, impressions, ctr, position). Note: This is usually automatically fetched via API.")
        up_gsc = st.file_uploader("Upload GSC CSV", type="csv", key="up_gsc")
        if up_gsc:
            try:
                df_gsc = safe_read_csv(up_gsc)
                st.write("**Data Preview:**")
                st.dataframe(df_gsc.head())
                if st.button("Submit to Database", key="btn_gsc"):
                    with st.spinner("Saving to database..."):
                        if engine:
                            df_gsc.to_sql('gsc_advanced_report', engine, if_exists='append', index=False)
                            st.success(f"Successfully saved {len(df_gsc)} rows!")
            except Exception as e:
                st.error(f"Error: {e}")

# End of app
