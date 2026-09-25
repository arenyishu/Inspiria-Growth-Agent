from datetime import datetime

def generate_weekly_report(ai_analysis):
    """Converts the AI JSON into a clean readable markdown report."""
    
    if not ai_analysis:
        return "Report generation failed due to missing AI analysis."
        
    date_str = datetime.now().strftime('%B %d, %Y')
        
    report = f"""
# Inspiria AI Growth Report
**Date:** {date_str}
**Priority Level:** {ai_analysis.get('priority', 'Medium')}

### Executive Summary
{ai_analysis.get('summary', '')}

### 🏆 Top Wins
"""
    for win in ai_analysis.get('wins', []):
        report += f"- {win}\n"
        
    report += "\n### 🚨 Important Issues\n"
    for issue in ai_analysis.get('issues', []):
        report += f"- {issue}\n"

    report += "\n### 🔍 Possible Causes & Opportunities\n"
    for cause in ai_analysis.get('possible_causes', []):
        report += f"- {cause}\n"
    for opp in ai_analysis.get('opportunities', []):
        report += f"- {opp}\n"
        
    report += "\n### 🚀 Recommended Actions\n"
    for action in ai_analysis.get('recommended_actions', []):
        report += f"- {action}\n"
        
    return report
