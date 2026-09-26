import google.generativeai as genai
import json
import streamlit as st
import os

def analyze_growth_data(evidence_package):
    \"\"\"Sends the structured evidence to the LLM for analysis and recommendation.\"\"\"
    
    # Safely get the key from Streamlit secrets, then fallback to os.environ
    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
    except:
        api_key = None
        
    if not api_key:
        from config.settings import GEMINI_API_KEY
        api_key = GEMINI_API_KEY
        
    if not api_key:
        st.error("Error: GEMINI_API_KEY is missing from Streamlit Secrets or .env")
        return None
        
    try:
        genai.configure(api_key=api_key)
        
        # Using the flash model for speed in the MVP
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f\"\"\"
        You are the Inspiria AI Growth Agent. Your job is to analyze marketing data and provide actionable intelligence.
        
        Here is the exact data for the last 7 days compared to the previous 7 days:
        {json.dumps(evidence_package, indent=2)}
        
        Analyze this data following these STRICT rules:
        1. Distinguish between 'Observed fact' and 'Possible explanation'. Do not state a cause as fact unless proven.
        2. Use wording like 'Data indicates...', 'Potential contributor...', 'Investigate...'
        3. Output your response ONLY as a valid JSON object matching the schema below. No markdown formatting outside the JSON, just the raw JSON string.

        JSON Schema:
        {{
          "summary": "Short executive summary of overall performance.",
          "wins": ["List of observed improvements"],
          "issues": ["List of significant declines or anomalies"],
          "opportunities": ["List of SEO or growth opportunities to investigate"],
          "possible_causes": ["List of possible explanations for the issues/wins"],
          "recommended_actions": ["Specific next steps for the marketing team"],
          "priority": "High | Medium | Low"
        }}
        \"\"\"
        
        response = model.generate_content(prompt)
        text_response = response.text
        
        # Clean up potential markdown code blocks around the JSON
        if text_response.startswith("`json"):
            text_response = text_response[7:-3]
        elif text_response.startswith("`"):
            text_response = text_response[3:-3]
            
        return json.loads(text_response.strip())
        
    except Exception as e:
        st.error(f"AI Analysis Error: {str(e)}")
        print(f"AI Analysis Error: {e}")
        return None
