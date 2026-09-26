import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from datetime import datetime
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

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
            <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #333; line-height: 1.6; max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="text-align: center; margin-bottom: 20px;">
                    <h2 style="color: #1A73E8; margin-bottom: 5px;">📈 Inspiria Weekly Growth Report</h2>
                    <p style="color: #5f6368; font-size: 14px; margin-top: 0;">Automated Data Extraction via GA4 & GSC APIs</p>
                </div>
                
                <h3 style="background-color: #f8f9fa; border-left: 4px solid #188038; padding: 10px 15px; margin-top: 20px;">🔍 Google Search Console (SEO)</h3>
                <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
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

                <h3 style="background-color: #f8f9fa; border-left: 4px solid #1da1f2; padding: 10px 15px; margin-top: 20px;">📱 Social Media Impact</h3>
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
                <p style="font-size: 11px; color: #999; text-align: center;">This report was securely generated by the Inspiria AI Growth Agent using Official Google APIs.</p>
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
