from config.settings import THRESHOLDS

def classify_change(change_pct):
    """Classifies a percentage change based on configured thresholds."""
    if change_pct <= THRESHOLDS["STRONG_DECLINE"]:
        return "STRONG_DECLINE"
    elif change_pct <= THRESHOLDS["WARNING_DECLINE"]:
        return "WARNING"
    elif change_pct >= THRESHOLDS["GROWTH"]:
        return "GROWTH"
    else:
        return "STABLE"

def run_detection_rules(evidence_package):
    """Analyzes the evidence package to detect specific rules and opportunities."""
    
    signals = []
    
    ga4 = evidence_package.get("ga4_performance", {})
    gsc = evidence_package.get("gsc_performance", {})
    
    # ---------------------------------------------------------
    # Rule 1: Traffic Decline (from Product Requirements)
    # ---------------------------------------------------------
    gsc_clicks_change = gsc.get("clicks", {}).get("change_pct", 0)
    classification = classify_change(gsc_clicks_change)
    if classification == "STRONG_DECLINE":
        signals.append({
            "type": "ISSUE",
            "detector": "Traffic Decline",
            "message": f"Organic search clicks dropped severely by {gsc_clicks_change}%. Immediate SEO investigation required (Check seasonality, ranking drops, or indexing issues)."
        })
    elif classification == "WARNING":
        signals.append({
            "type": "WARNING",
            "detector": "Traffic Warning",
            "message": f"Organic search clicks are trending down by {gsc_clicks_change}%."
        })
        
    # ---------------------------------------------------------
    # Rule 2: Conversion Mismatch (from Product Requirements)
    # ---------------------------------------------------------
    ga4_sessions_change = ga4.get("sessions", {}).get("change_pct", 0)
    ga4_conv_change = ga4.get("conversions", {}).get("change_pct", 0)
    
    if ga4_sessions_change > 0 and ga4_conv_change <= THRESHOLDS["WARNING_DECLINE"]:
        signals.append({
            "type": "ISSUE",
            "detector": "Conversion Mismatch",
            "message": f"Traffic increased by {ga4_sessions_change}% but conversions dropped by {ga4_conv_change}%. Investigate landing page intent, broken forms, or tracking."
        })
        
    # ---------------------------------------------------------
    # Rule 3: Growth Detection
    # ---------------------------------------------------------
    if ga4_conv_change >= THRESHOLDS["GROWTH"]:
        signals.append({
            "type": "WIN",
            "detector": "Conversion Growth",
            "message": f"Conversions grew by a healthy {ga4_conv_change}%. Identify which channels drove this and scale."
        })
        
    return signals
