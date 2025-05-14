import requests
import os

DEEPL_API_KEY = os.getenv('DEEPL_API_KEY')

def translate_deepl(text):
    url = "https://api-free.deepl.com/v2/translate"
    params = {
        "auth_key": DEEPL_API_KEY,
        "text": text,
        "source_lang": "EN",
        "target_lang": "TR"
    }
    r = requests.post(url, data=params)
    result = r.json()
    return result['translations'][0]['text']
