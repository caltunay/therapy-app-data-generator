from flask import Flask, render_template, request, redirect, url_for
import random
import requests
import os
from dotenv import load_dotenv

load_dotenv()

UNSPLASH_ACCESS_KEY = os.getenv('UNSPLASH_API_KEY')
PIXABAY_API_KEY = os.getenv('PIXABAY_API_KEY')
PEXELS_API_KEY = os.getenv('PEXELS_API_KEY') 

DEEPL_API_KEY = os.getenv('DEEPL_API_KEY')

SUPABASE_PB_KEY = os.getenv('SUPABASE_ANON_PUBLIC_KEY')
SUPABASE_URL = os.getenv('SUPABASE_PROJECT_URL')
SUPABASE_TABLE = "speech-therapy-data" 

AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')

app = Flask(__name__)

# Load words once
with open('word_list.txt', 'r', encoding='utf-8') as f:
    WORD_LIST = [w.strip() for w in f if w.strip()]

def get_pexels_image(word):
    headers = {'Authorization': PEXELS_API_KEY}
    params = {'query': word, 'per_page':1}

    response = requests.get('https://api.pexels.com/v1/search', headers=headers, params=params)
    data = response.json()
    
    if len(data['photos']) > 0:
        return data['photos'][0]['src']['original']
    else:
        return None

def get_unsplash_image(word):
    url = f"https://api.unsplash.com/search/photos?query={word}&client_id={UNSPLASH_ACCESS_KEY}"
    r = requests.get(url)
    if r.status_code != 200:
        return None
    data = r.json()
    if data.get('results'):
        return data['results'][0]['urls']['small']
    return None

# unsplash images are much better but api has a limit
def get_pixabay_image(word):
    url = f"https://pixabay.com/api/?key={PIXABAY_API_KEY}&q={word}&image_type=photo"
    response = requests.get(url)
    data = response.json()
    if data['hits']:
        return data['hits'][0]['largeImageURL']
    else:
        return None

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

def save_to_supabase(imgur_url, word, translation):
    headers = {
        "apikey": SUPABASE_PB_KEY,
        "Authorization": f"Bearer {SUPABASE_PB_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "image_url": imgur_url,
        "eng_word": word,
        "tr_word": translation  
    }

    response = requests.post(
        f"{SUPABASE_URL}/rest/v1/{SUPABASE_TABLE}",
        headers=headers,
        json=data
    )

@app.route('/')
def home():
    word = random.choice(WORD_LIST).title()
    
    image_providers = [get_pexels_image, get_unsplash_image, get_pixabay_image]
    
    for provider_func in image_providers:
        image_url = provider_func(word)
        if image_url: 
            break
    # image_url = get_pexels_image(word)
    # try unsplash first
    # image_url = get_unsplash_image(word)
    # if not image_url:
    #     # if unsplash fails, try pixabay    
    #     image_url = get_pixabay_image(word)
    translation = translate_deepl(word).title()
    return render_template('index.html', word=word, image_url=image_url, translation=translation)

@app.route('/upload', methods=['POST'])
def upload():
    image_url = request.form['image_url']
    word = request.form['word']
    translation = request.form['translation']

    save_to_supabase(image_url, word, translation)
    return redirect(url_for('home'))

@app.route('/reject', methods=['POST'])
def reject():
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)