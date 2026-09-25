import os
from config.settings import GA4_PROPERTY_ID, GSC_SITE_URL
from extractors.ga4_client import get_ga4_data
from extractors.gsc_client import get_gsc_data
from engines.kpi_engine import compare_ga4_periods, compare_gsc_periods
from datetime import datetime, timedelta
import json

def main():
    print("🚀 Starting Inspiria AI Growth Agent Workflow...\n")
    
    if not GA4_PROPERTY_ID or not GSC_SITE_URL:
        print("❌ ERROR: Missing configuration.")
        return

    # -----------------------------------------
    # STEP 1 & 2: FETCH DATA (Current vs Previous)
    # -----------------------------------------
    print("--- Fetching Data (Current 7 Days vs Previous 7 Days) ---")
    
    # Dates for GSC (YYYY-MM-DD format)
    today = datetime.now()
    cur_end = today.strftime('%Y-%m-%d')
    cur_start = (today - timedelta(days=7)).strftime('%Y-%m-%d')
    
    prev_end = (today - timedelta(days=8)).strftime('%Y-%m-%d')
    prev_start = (today - timedelta(days=14)).strftime('%Y-%m-%d')
    
    # Fetch GA4
    ga4_cur = get_ga4_data(start_date="7daysAgo", end_date="today")
    ga4_prev = get_ga4_data(start_date="14daysAgo", end_date="8daysAgo")
    
    # Fetch GSC
    gsc_cur = get_gsc_data(start_date=cur_start, end_date=cur_end)
    gsc_prev = get_gsc_data(start_date=prev_start, end_date=prev_end)

    # -----------------------------------------
    # STEP 3: CALCULATE KPIs
    # -----------------------------------------
    print("\n--- Step 3: Calculating KPIs ---")
    
    ga4_kpis = compare_ga4_periods(ga4_cur, ga4_prev)
    gsc_kpis = compare_gsc_periods(gsc_cur, gsc_prev)
    
    # Combine into a structured dictionary (Evidence Package for AI)
    evidence_package = {
        "ga4_performance": ga4_kpis,
        "gsc_performance": gsc_kpis
    }
    
    print("\n✅ KPI Engine Output (Structured Evidence):")
    print(json.dumps(evidence_package, indent=2))

    # -----------------------------------------
    # STEP 4: RUN DETECTION RULES
    # -----------------------------------------
    print("\n--- Step 4: Running Detection Rules ---")
    from engines.rules_engine import run_detection_rules
    
    detected_signals = run_detection_rules(evidence_package)
    evidence_package["detected_signals"] = detected_signals
    
    for signal in detected_signals:
        icon = "🚨" if signal["type"] == "ISSUE" else "✅"
        print(f"{icon} [{signal['type']}] {signal['detector']}: {signal['message']}")

    # -----------------------------------------
    # STEP 5 & 6: AI ANALYSIS & REPORTING
    # -----------------------------------------
    print("\n--- Step 5: Sending to AI Analyst ---")
    print("Wait a few seconds while Gemini analyzes the data...")
    from ai_layer.analyst import analyze_growth_data
    from reporters.markdown_report import generate_weekly_report
    
    ai_json = analyze_growth_data(evidence_package)
    
    if ai_json:
        print("\n✅ AI Analysis Complete!")
        
        print("\n--- Step 6: Generating Report ---")
        final_report = generate_weekly_report(ai_json)
        
        # Save JSON state for the Dashboard
        with open("latest_data.json", "w", encoding="utf-8") as f:
            json.dump({
                "evidence": evidence_package,
                "ai_analysis": ai_json,
                "date": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }, f, indent=2)
        
        # Save the report to a file
        report_filename = f"Growth_Report_{datetime.now().strftime('%Y-%m-%d')}.md"
        with open(report_filename, "w", encoding="utf-8") as f:
            f.write(final_report)
            
        print(f"\n🎉 Workflow Complete! Report saved to {report_filename}")
        print("\n--- REPORT PREVIEW ---\n")
        print(final_report)
    else:
        print("❌ AI Analysis failed. Cannot generate report.")

if __name__ == "__main__":
    main()
