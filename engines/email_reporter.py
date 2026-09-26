import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from datetime import datetime
import streamlit as st

def send_weekly_report(data_dict):
    """
    Sends the weekly SEO & Analytics report via Gmail SMTP.
    data_dict contains the week's metrics.
    """
    try:
        try:
            sender_email = st.secrets['SMTP_SENDER_EMAIL']
            sender_password = st.secrets['SMTP_SENDER_PASSWORD']
            receivers = st.secrets['SMTP_RECEIVERS'].split(',')
        except Exception:
            sender_email = os.environ.get('SMTP_SENDER_EMAIL')
            sender_password = os.environ.get('SMTP_SENDER_PASSWORD')
            receivers = os.environ.get('SMTP_RECEIVERS', '').split(',')
            
        if not sender_email or not sender_password or not receivers:
            print("❌ SMTP Credentials missing. Cannot send email.")
            return False

        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"📈 Inspiria Weekly Growth Report ({datetime.now().strftime('%Y-%m-%d')})"
        msg["From"] = sender_email
        msg["To"] = ", ".join(receivers)

        # Build HTML Email
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
                <h2 style="color: #1A73E8;">Inspiria Weekly Growth Report</h2>
                <p>Here is the automated SEO and Analytics breakdown for the past 7 days.</p>
                
                <h3 style="background-color: #f1f3f4; padding: 10px; border-radius: 5px; color: #d93025;">⚙️ TECH SEO</h3>
                <ul style="list-style-type: none; padding-left: 10px;">
                    <li><b>Pages Crawled:</b> {data_dict.get('pages_crawled', 'N/A')}</li>
                    <li><b>Total Crawl Errors:</b> {data_dict.get('total_crawl_errors', 'N/A')}</li>
                    <li><b>Indexed Pages:</b> {data_dict.get('indexed_pages', 'N/A')}</li>
                    <li><b>Index Coverage Errors:</b> {data_dict.get('index_coverage_errors', 'N/A')}</li>
                    <li><b>Broken Links:</b> {data_dict.get('broken_links', 'N/A')}</li>
                    <li><b>5xx Errors:</b> {data_dict.get('server_errors_5xx', 'N/A')}</li>
                    <li><b>Avg LCP:</b> {data_dict.get('avg_lcp', 'N/A')}</li>
                    <li><b>Avg INP / FID:</b> {data_dict.get('avg_inp', 'N/A')}</li>
                    <li><b>Avg CLS:</b> {data_dict.get('avg_cls', 'N/A')}</li>
                    <li><b>Mobile Usability Issues:</b> {data_dict.get('mobile_usability_issues', 'N/A')}</li>
                    <li><b>Duplicate Pages:</b> {data_dict.get('duplicate_pages', 'N/A')}</li>
                    <li><b>hreflang Errors:</b> {data_dict.get('hreflang_errors', 'N/A')}</li>
                    <li><b>Sitemap Errors:</b> {data_dict.get('sitemap_errors', 'N/A')}</li>
                    <li><b>Tech SEO Score:</b> {data_dict.get('tech_seo_score', 'N/A')}</li>
                </ul>

                <h3 style="background-color: #f1f3f4; padding: 10px; border-radius: 5px; color: #188038;">📄 ON-PAGE SEO</h3>
                <ul style="list-style-type: none; padding-left: 10px;">
                    <li><b>Total Keywords Ranking:</b> {data_dict.get('total_keywords', 'N/A')}</li>
                    <li><b>Keywords in Top 3:</b> {data_dict.get('keywords_top_3', 'N/A')}</li>
                    <li><b>Keywords in Top 10:</b> {data_dict.get('keywords_top_10', 'N/A')}</li>
                    <li><b>Avg Keyword Position:</b> {data_dict.get('avg_keyword_position', 'N/A')}</li>
                    <li><b>Impressions:</b> {data_dict.get('impressions', 'N/A')}</li>
                    <li><b>Clicks:</b> {data_dict.get('clicks', 'N/A')}</li>
                    <li><b>Avg CTR:</b> {data_dict.get('avg_ctr', 'N/A')}%</li>
                    <li><b>Organic Sessions:</b> {data_dict.get('organic_sessions', 'N/A')}</li>
                    <li><b>Avg Time on Page:</b> {data_dict.get('avg_time_on_page', 'N/A')}s</li>
                    <li><b>Bounce Rate:</b> {data_dict.get('bounce_rate', 'N/A')}%</li>
                    <li><b>Internal Links Added:</b> {data_dict.get('internal_links_added', 'N/A')}</li>
                    <li><b>Leads from Organic:</b> {data_dict.get('leads_from_organic', 'N/A')}</li>
                </ul>

                <h3 style="background-color: #f1f3f4; padding: 10px; border-radius: 5px; color: #1967d2;">🔗 OFF-PAGE SEO</h3>
                <ul style="list-style-type: none; padding-left: 10px;">
                    <li><b>Total Backlinks:</b> {data_dict.get('total_backlinks', 'N/A')}</li>
                    <li><b>New Backlinks:</b> {data_dict.get('new_backlinks', 'N/A')}</li>
                    <li><b>Lost Backlinks:</b> {data_dict.get('lost_backlinks', 'N/A')}</li>
                    <li><b>Referring Domains:</b> {data_dict.get('referring_domains', 'N/A')}</li>
                    <li><b>New Referring Domains:</b> {data_dict.get('new_referring_domains', 'N/A')}</li>
                    <li><b>Avg Domain Rating (DR):</b> {data_dict.get('avg_dr', 'N/A')}</li>
                    <li><b>Brand Mentions:</b> {data_dict.get('brand_mentions', 'N/A')}</li>
                </ul>
                
                <hr>
                <p style="font-size: 12px; color: #777; text-align: center;">This report was automatically generated by the Inspiria AI Growth Agent.</p>
            </body>
        </html>
        """
        
        msg.attach(MIMEText(html_content, "html"))

        print("Connecting to Gmail SMTP...")
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            # We remove spaces from the app password if the user copied them
            server.login(sender_email, sender_password.replace(' ', ''))
            server.sendmail(sender_email, receivers, msg.as_string())
            
        print(f"Weekly report emailed successfully to {len(receivers)} recipients!")
        return True
        
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False
