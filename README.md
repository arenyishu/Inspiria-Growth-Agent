# Inspiria AI Growth Agent 🚀

An autonomous, AI-powered Growth and SEO Analytics dashboard built for Inspiria Knowledge Campus. This agent acts as a 24/7 digital marketing analyst—automatically ingesting data from Google's APIs, analyzing search intents with LLMs, and uncovering technical SEO bottlenecks.

## 🌟 Key Features

*   **Automated Data Ingestion pipeline:** Nightly cron jobs securely pull data via official APIs from **Google Search Console** and **Google Analytics 4**.
*   **AI-Powered SEO Tagging (Phase 2):** Uses the Gemini 1.5 Flash Lite API to automatically analyze thousands of unbranded search queries, tagging them by **Search Intent** (Informational, Commercial, Navigational) and **Topic Cluster**.
*   **The Content Command Center (Phase 3):** An advanced SEO data lake that merges real Google Search Console traffic with technical **SEMrush Site Audits** via SQL JOINs, instantly identifying High-Traffic Orphan Pages and Slow-Loading Conversion Engines.
*   **Universal Data Ingestion Hub:** A secure, manual fallback UI for uploading offline CRM data, native Social Media metrics, and external SEO exports.
*   **Weekly Executive AI Analyst:** A GitHub Actions cron job that analyzes week-over-week performance changes and automatically emails an executive summary to stakeholders every Monday morning.

## 🏗️ Tech Stack

*   **Frontend:** Streamlit (Python)
*   **Database:** Supabase (PostgreSQL)
*   **AI / LLM:** Google Gemini REST API
*   **Integrations:** Google Search Console API, Google Analytics 4 API, UptimeRobot
*   **Automation:** GitHub Actions (CI/CD & Cron Scheduling)

## 🗄️ Database Architecture

The application relies on a cloud-hosted Supabase PostgreSQL warehouse containing the following core tables:
*   gsc_advanced_report (Real-time organic search queries and landing pages)
*   ga4_daily & ga4_channels (Web traffic and referral channels)
*   semrush_site_audit (Page-level technical SEO metrics)
*   i_keyword_tags (LLM-generated keyword classifications)
*   ction_register (Automated and manual marketing tasks)

## 🔒 Security
All API keys, Service Account JSONs, and Database URIs are strictly managed via environment variables (.env locally) and Streamlit Secrets in production.

---
*Built autonomously via Agentic AI for the Inspiria Growth Team.*
