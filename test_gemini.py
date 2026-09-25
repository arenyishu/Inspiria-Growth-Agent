from dotenv import load_dotenv
import os
import google.generativeai as genai

load_dotenv()
api_key = os.environ.get('GEMINI_API_KEY')

if not api_key:
    print('Key missing!')
else:
    print('Testing key...')
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-flash-latest')
        response = model.generate_content("Reply with 'SUCCESS'")
        print(response.text)
    except Exception as e:
        print(f"Error: {e}")
