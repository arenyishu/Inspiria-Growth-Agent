import sys
import os
import json
import requests
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db_manager import get_untagged_queries, upsert_keyword_tags
from config.settings import GEMINI_API_KEY

def tag_keywords_batch():
    if not GEMINI_API_KEY:
        print('Error: GEMINI_API_KEY is not set.')
        return False
        
    queries = get_untagged_queries(limit=500)
    if not queries:
        print('No untagged queries found. All caught up!')
        return True
        
    print(f'Found {len(queries)} untagged queries. Sending to Gemini REST API...')
    
    url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent?key={GEMINI_API_KEY}'
    
    prompt = '''
    You are an expert SEO Strategist. I am giving you a list of search queries that users typed into Google to find our college (Inspiria Knowledge Campus).
    
    Your job is to analyze each query and assign 3 tags:
    1. "intent": Must be exactly one of: "Informational", "Transactional", "Navigational".
    2. "topic_cluster": Group the query into a logical content bucket (e.g., "BBA Admissions", "Hospitality Management", "General College Info", "Coding/Tech", etc). Keep cluster names short and consistent.
    3. "brand_status": Must be exactly one of: "Brand" (if the query contains words like inspiria, inperia, etc) or "Non-Brand".
    
    Return a strictly valid JSON array of objects.
    Example output:
    [
      {"query": "bba colleges in siliguri", "intent": "Transactional", "topic_cluster": "BBA Admissions", "brand_status": "Non-Brand"},
      {"query": "inspiria knowledge campus reviews", "intent": "Navigational", "topic_cluster": "Brand Reputation", "brand_status": "Brand"}
    ]
    
    Here are the queries to analyze:
    ''' + json.dumps(queries)
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json"
        }
    }
    
    headers = {'Content-Type': 'application/json'}
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            print(f'Attempt {attempt+1} of {max_retries}...')
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            
            if response.status_code == 429:
                print(f"API Rate Limit hit (429). Waiting 35 seconds...")
                time.sleep(35)
                continue
                
            if response.status_code != 200:
                print(f"API Error {response.status_code}: {response.text}")
                return False
                
            data = response.json()
            raw_text = data['candidates'][0]['content']['parts'][0]['text']
            
            results = json.loads(raw_text)
            
            if not isinstance(results, list):
                print('Error: AI did not return a list.')
                return False
                
            print(f'Successfully tagged {len(results)} queries. Saving to database...')
            upsert_keyword_tags(results)
            print('Batch saved successfully!')
            return True
            
        except Exception as e:
            print(f'AI Tagging Error: {e}')
            return False

if __name__ == '__main__':
    tag_keywords_batch()
