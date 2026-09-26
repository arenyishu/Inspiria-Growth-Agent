import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import importlib
import database.db_manager
importlib.reload(database.db_manager)
from database.db_manager import get_historical_data, save_ai_insights, get_latest_ai_insights
from engines.kpi_engine import calculate_percentage_change
from ai_layer.analyst import analyze_growth_data
import os
import plotly.express as px

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
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Executive Scorecard", "Action Register", "Reports", "Data Sources", "Data Ingestion"])

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

    c_reach = get_totals(social_cur, 'daily_reach')
    p_reach = get_totals(social_prev, 'daily_reach')
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
{format_row('Social Reach', c_reach, p_reach, chg_reach, t_reach)}
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
        stage=["Top of Funnel (Awareness: Social Reach + Search Impressions)", "Middle of Funnel (Interest: Search Clicks)", "Website Traffic (GA4 Sessions)", "Bottom of Funnel (GA4 Active Users)"]
    )
    if funnel_data['number'][0] > 0:
        fig_funnel = px.funnel(funnel_data, x='number', y='stage')
        fig_funnel.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=350, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#80868B'))
        fig_funnel.update_traces(marker=dict(color=['#5c6bc0', '#42a5f5', '#26c6da', '#66bb6a']))
        st.plotly_chart(fig_funnel, use_container_width=True)
    else:
        st.info("Upload social data or ensure search data exists to view the funnel.")

    # --- SEMRUSH AUTHORITY ---
    st.markdown("<br><h2 style='font-size: 20px; color: var(--text-color); margin-bottom: 20px;'>SEO & Authority (SEMrush)</h2>", unsafe_allow_html=True)
    if not semrush_cur.empty:
        col_seo1, col_seo2 = st.columns(2)
        
        with col_seo1:
            fig_auth = px.line(semrush_cur, x='date', y='authority_score', 
                              title="Authority Score Trend",
                              labels={"authority_score": "Authority Score", "date": "Date"},
                              color_discrete_sequence=['#ff7043'])
            fig_auth.update_layout(
                margin=dict(l=0, r=0, t=40, b=0),
                height=300,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#80868B")
            )
            # Make the y-axis not start at zero so the growth is visible
            fig_auth.update_yaxes(range=[semrush_cur['authority_score'].min() - 2, semrush_cur['authority_score'].max() + 2])
            st.plotly_chart(fig_auth, use_container_width=True, config={'displayModeBar': False})
            
        with col_seo2:
            fig_kw = px.area(semrush_cur, x='date', y='organic_keywords', 
                              title="Organic Keywords Trend",
                              labels={"organic_keywords": "Total Keywords", "date": "Date"},
                              color_discrete_sequence=['#8d6e63'])
            fig_kw.update_layout(
                margin=dict(l=0, r=0, t=40, b=0),
                height=300,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#80868B")
            )
            # Make the y-axis scaled nicely
            fig_kw.update_yaxes(range=[semrush_cur['organic_keywords'].min() - 50, semrush_cur['organic_keywords'].max() + 50])
            st.plotly_chart(fig_kw, use_container_width=True, config={'displayModeBar': False})
    else:
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

with tab2:
    st.header("Action Register")
    st.write("Track strategic marketing tasks assigned by the AI Analyst.")
    
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

    from database.db_manager import get_action_tasks, update_action_task
    tasks_df = get_action_tasks()
    if not tasks_df.empty:
        for _, row in tasks_df.iterrows():
            with st.container():
                c1, c2, c3, c4 = st.columns([4, 1, 1, 1])
                c1.write(f"**{row['task_name']}**")
                c2.write(f"*{row['priority']}*")
                c3.write(f"{row['status']}")
                if row['status'] != 'Done':
                    if c4.button("✓ Done", key=f"done_{row['task_id']}"):
                        update_action_task(row['task_id'], 'Done')
                        st.rerun()
                else:
                    c4.write("✅")
                st.markdown("<hr style='margin: 0.5em 0;'>", unsafe_allow_html=True)
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
    
    st.subheader("Social Media (Meta / LinkedIn)")
    if not social_cur.empty:
        st.dataframe(social_cur)
    else:
        st.info("No Social Media data available for this period. Upload data in the Data Ingestion tab.")

    st.subheader("SEMrush (SEO & Authority)")
    if not semrush_cur.empty:
        st.dataframe(semrush_cur)
    else:
        st.info("No SEMrush data available for this period.")

with tab5:
    st.header("Data Ingestion")
    st.write("Upload CSV files or manually enter daily data to push it to the Supabase Data Warehouse.")
    
    with st.expander("📊 Google Analytics 4 (Website Traffic)"):
        st.write("Automatically synced via API, but you can manually override or add historic data here:")
        with st.form("ga4_manual"):
            c1, c2 = st.columns(2)
            m_date = c1.date_input("Date", key="ga4_date")
            m_sess = c2.number_input("Sessions", min_value=0)
            m_users = c1.number_input("Active Users", min_value=0)
            m_views = c2.number_input("Pageviews", min_value=0)
            m_conv = c1.number_input("Conversions", min_value=0)
            if st.form_submit_button("Save GA4 Data"):
                import pandas as pd
                from database.db_manager import upsert_ga4_data
                df = pd.DataFrame([{
                    "date": m_date.strftime('%Y-%m-%d'),
                    "sessions": m_sess,
                    "active_users": m_users,
                    "pageviews": m_views,
                    "conversions": m_conv
                }])
                upsert_ga4_data(df)
                st.success("GA4 data saved!")

    with st.expander("🔍 Google Search Console (SEO)"):
        st.write("Automatically synced via API, but you can manually override or add historic data here:")
        with st.form("gsc_manual"):
            c1, c2 = st.columns(2)
            m_date = c1.date_input("Date", key="gsc_date")
            m_clicks = c2.number_input("Clicks", min_value=0)
            m_imp = c1.number_input("Impressions", min_value=0)
            if st.form_submit_button("Save GSC Data"):
                import pandas as pd
                from database.db_manager import upsert_gsc_data
                df = pd.DataFrame([{"date": m_date.strftime('%Y-%m-%d'), "clicks": m_clicks, "impressions": m_imp}])
                upsert_gsc_data(df)
                st.success("GSC data saved!")

    with st.expander("📱 Social Media (Meta / LinkedIn)"):
        st.write("Upload a CSV export from your social tools, or enter manually below.")
        uploaded_file = st.file_uploader("Upload Social Data (CSV)", type="csv")
        if uploaded_file is not None:
            try:
                import pandas as pd
                df = pd.read_csv(uploaded_file)
                st.dataframe(df.head())
                if st.button("Save CSV to Database", type="primary", key="btn_soc"):
                    from database.db_manager import upsert_social_data
                    upsert_social_data(df)
                    st.success("Social CSV warehoused!")
            except Exception as e:
                st.error(f"Error reading CSV: {e}")
        
        st.markdown("#### Manual Entry")
        with st.form("social_manual"):
            c1, c2 = st.columns(2)
            m_date = c1.date_input("Date", key="soc_date")
            m_foll = c2.number_input("Total Followers", min_value=0)
            m_reach = c1.number_input("Daily Reach", min_value=0)
            m_eng = c2.number_input("Daily Engagement", min_value=0)
            if st.form_submit_button("Save Social Data"):
                import pandas as pd
                from database.db_manager import upsert_social_data
                df = pd.DataFrame([{"date": m_date.strftime('%Y-%m-%d'), "followers": m_foll, "reach": m_reach, "engagement": m_eng}])
                upsert_social_data(df)
                st.success("Social data saved!")

    with st.expander("📈 SEMrush (SEO & Authority)"):
        st.write("Manually log your SEMrush rankings here if you do not have the API add-on.")
        with st.form("semrush_manual"):
            c1, c2 = st.columns(2)
            m_date = c1.date_input("Date", key="sem_date")
            m_auth = c2.number_input("Authority Score", min_value=0)
            m_links = c1.number_input("Total Backlinks", min_value=0)
            m_ref = c2.number_input("Referring Domains", min_value=0)
            m_org = c1.number_input("Organic Keywords", min_value=0)
            m_cost = c2.number_input("Traffic Cost ($)", min_value=0)
            if st.form_submit_button("Save SEMrush Data"):
                import pandas as pd
                from database.db_manager import upsert_semrush_data
                df = pd.DataFrame([{
                    "date": m_date.strftime('%Y-%m-%d'), 
                    "authority_score": m_auth, 
                    "total_backlinks": m_links, 
                    "referring_domains": m_ref, 
                    "organic_keywords": m_org, 
                    "traffic_cost": m_cost
                }])
                upsert_semrush_data(df)
                st.success("SEMrush data saved!")
                
    with st.expander("💼 CRM Conversions (Pipeline)"):
        st.write("Upload your leads/sales from HubSpot, Salesforce, etc.")
        uploaded_crm = st.file_uploader("Upload CRM Data (CSV)", type="csv", key="crm_up")
        if uploaded_crm is not None:
            try:
                import pandas as pd
                crm_df_up = pd.read_csv(uploaded_crm)
                st.dataframe(crm_df_up.head())
                if st.button("Save to Pipeline", type="primary", key="btn_crm"):
                    from database.db_manager import upsert_crm_conversions
                    upsert_crm_conversions(crm_df_up)
                    st.success("CRM Data warehoused!")
            except Exception as e:
                st.error(f"Error reading CRM CSV: {e}")
