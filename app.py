from flask import Flask, render_template, request, redirect, url_for
import random
import requests
import os
import csv
from dotenv import load_dotenv

load_dotenv()

# UNSPLASH_ACCESS_KEY = os.getenv('UNSPLASH_API_KEY')
DEEPL_API_KEY = os.getenv('DEEPL_API_KEY')
IMGUR_CLIENT_ID = os.getenv('IMGUR_CLIENT_ID')
PIXABAY_API_KEY = os.getenv('PIXABAY_API_KEY')

SUPABASE_PB_KEY = os.getenv('SUPABASE_ANON_PUBLIC_KEY')
SUPABASE_URL = os.getenv('SUPABASE_PROJECT_URL')
SUPABASE_TABLE = "speech-therapy-data" 

app = Flask(__name__)

# Load words once
with open('word_list.txt', 'r', encoding='utf-8') as f:
    WORD_LIST = [w.strip() for w in f if w.strip()]

# def get_unsplash_image(word):
#     url = f"https://api.unsplash.com/search/photos?query={word}&client_id={UNSPLASH_ACCESS_KEY}"
#     r = requests.get(url)
#     data = r.json()
#     if data.get('results'):
#         return data['results'][0]['urls']['small']
#     return None

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

def upload_to_imgur(image_url):
    headers = {'Authorization': f'Client-ID {IMGUR_CLIENT_ID}'}
    data = {'image': image_url, 'type': 'url'}
    r = requests.post('https://api.imgur.com/3/image', headers=headers, data=data)
    if r.status_code == 200:
        return r.json()['data']['link']
    return None

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
    image_url = get_pixabay_image(word)
    translation = translate_deepl(word).title()
    return render_template('index.html', word=word, image_url=image_url, translation=translation)

@app.route('/upload', methods=['POST'])
def upload():
    image_url = request.form['image_url']
    word = request.form['word']
    translation = request.form['translation']
    imgur_url = upload_to_imgur(image_url)

    final_url = imgur_url if imgur_url else image_url
    if not imgur_url:
        print(f"Imgur upload failed for {image_url}, saving original URL.")

    save_to_supabase(final_url, word, translation)
    return redirect(url_for('home'))

@app.route('/reject', methods=['POST'])
def reject():
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)