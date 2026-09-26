import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv
import streamlit as st

load_dotenv()

def send_weekly_report(data_dict):
    try:
        try:
            smtp_user = st.secrets["SMTP_SENDER_EMAIL"]
            smtp_pass = st.secrets["SMTP_SENDER_PASSWORD"]
        except:
            smtp_user = os.environ.get("SMTP_SENDER_EMAIL")
            smtp_pass = os.environ.get("SMTP_SENDER_PASSWORD")
            
        if not smtp_user or not smtp_pass:
            print("Email Reporter Error: SMTP credentials not found.")
            return False

        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = "seo@inspiria.edu.in,rakesh.p@inspiria.edu.in"
        msg['Subject'] = "Inspiria AI Growth Agent - Weekly Automated Report"

        html_content = f"""
        <html>
            <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #333; line-height: 1.6; max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="text-align: center; margin-bottom: 20px;">
                    <h2 style="color: #1A73E8; margin-bottom: 5px;">📈 Inspiria Weekly Growth Report</h2>
                    <p style="color: #5f6368; font-size: 14px; margin-top: 0;">Automated Data Extraction via Official APIs</p>
                </div>
                
                <h3 style="background-color: #f8f9fa; border-left: 4px solid #d93025; padding: 10px 15px; margin-top: 20px;">⚙️ Core Web Vitals & Usability</h3>
                <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                    <tr style="border-bottom: 1px solid #eee;">
                        <td style="padding: 8px 0;"><b>Avg LCP:</b></td>
                        <td style="text-align: right; font-weight: bold;">{data_dict.get('avg_lcp', 'N/A')}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #eee;">
                        <td style="padding: 8px 0;"><b>Avg INP / FID:</b></td>
                        <td style="text-align: right; font-weight: bold;">{data_dict.get('avg_inp', 'N/A')}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #eee;">
                        <td style="padding: 8px 0;"><b>Avg CLS:</b></td>
                        <td style="text-align: right; font-weight: bold;">{data_dict.get('avg_cls', 'N/A')}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #eee;">
                        <td style="padding: 8px 0;"><b>Mobile Usability Issues:</b></td>
                        <td style="text-align: right; font-weight: bold; color: #d93025;">{data_dict.get('mobile_usability_issues', 'N/A')}</td>
                    </tr>
                </table>

                <h3 style="background-color: #f8f9fa; border-left: 4px solid #188038; padding: 10px 15px; margin-top: 20px;">🔍 Google Search Console (SEO)</h3>
                <table style="width: 100%; border-collapse: collapse; margin-bottom: 10px;">
                    <tr style="border-bottom: 1px solid #eee;">
                        <td style="padding: 8px 0;"><b>Total Impressions:</b></td>
                        <td style="text-align: right; font-weight: bold; color: #188038;">{data_dict.get('impressions', '0')}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #eee;">
                        <td style="padding: 8px 0;"><b>Total Clicks:</b></td>
                        <td style="text-align: right; font-weight: bold; color: #188038;">{data_dict.get('clicks', '0')}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #eee;">
                        <td style="padding: 8px 0;"><b>Average CTR:</b></td>
                        <td style="text-align: right; font-weight: bold;">{data_dict.get('avg_ctr', '0')}%</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #eee;">
                        <td style="padding: 8px 0;"><b>Avg Keyword Position:</b></td>
                        <td style="text-align: right; font-weight: bold;">{data_dict.get('avg_keyword_position', '0')}</td>
                    </tr>
                </table>
                
                <h4 style="margin-bottom: 5px;">🏆 Top Web Searches on Google</h4>
                <ul style="font-size: 14px; margin-top: 0; padding-left: 20px;">
                    {data_dict.get('top_queries_html', '<li>No data</li>')}
                </ul>
                
                <h4 style="margin-bottom: 5px;">🔥 Top Performing Content on Google</h4>
                <ul style="font-size: 14px; margin-top: 0; padding-left: 20px;">
                    {data_dict.get('top_pages_html', '<li>No data</li>')}
                </ul>

                <h3 style="background-color: #f8f9fa; border-left: 4px solid #f29900; padding: 10px 15px; margin-top: 20px;">📊 Google Analytics 4 (Traffic)</h3>
                <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                    <tr style="border-bottom: 1px solid #eee;">
                        <td style="padding: 8px 0;"><b>Total Sessions:</b></td>
                        <td style="text-align: right; font-weight: bold; color: #f29900;">{data_dict.get('organic_sessions', '0')}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #eee;">
                        <td style="padding: 8px 0;"><b>Total Pageviews:</b></td>
                        <td style="text-align: right; font-weight: bold;">{data_dict.get('pageviews', '0')}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #eee;">
                        <td style="padding: 8px 0;"><b>Bounce Rate:</b></td>
                        <td style="text-align: right; font-weight: bold;">{data_dict.get('bounce_rate', '0')}%</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #eee;">
                        <td style="padding: 8px 0;"><b>Avg Time on Page:</b></td>
                        <td style="text-align: right; font-weight: bold;">{data_dict.get('avg_time_on_page', '0')}s</td>
                    </tr>
                </table>

                <h3 style="background-color: #f8f9fa; border-left: 4px solid #1da1f2; padding: 10px 15px; margin-top: 20px;">📱 Overall Social Media Performance</h3>
                <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                    <tr style="border-bottom: 1px solid #eee;">
                        <td style="padding: 8px 0;"><b>Total Followers:</b></td>
                        <td style="text-align: right; font-weight: bold; color: #1da1f2;">{data_dict.get('social_followers', '0')}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #eee;">
                        <td style="padding: 8px 0;"><b>Total Reach:</b></td>
                        <td style="text-align: right; font-weight: bold;">{data_dict.get('social_reach', '0')}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #eee;">
                        <td style="padding: 8px 0;"><b>Engagement Count:</b></td>
                        <td style="text-align: right; font-weight: bold;">{data_dict.get('social_engagement', '0')}</td>
                    </tr>
                </table>
                
                <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0 15px 0;">
                <p style="font-size: 11px; color: #999; text-align: center;">This report was securely generated by the Inspiria AI Growth Agent.</p>
            </body>
        </html>
        """
        
        msg.attach(MIMEText(html_content, 'html'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False
