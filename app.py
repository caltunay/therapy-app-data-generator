from flask import Flask, render_template, request, redirect, url_for, session
import requests
import boto3
import os
from dotenv import load_dotenv
import random
import uuid

load_dotenv()

UNSPLASH_ACCESS_KEY = os.getenv('UNSPLASH_API_KEY')
PIXABAY_API_KEY = os.getenv('PIXABAY_API_KEY')
PEXELS_API_KEY = os.getenv('PEXELS_API_KEY') 

DEEPL_API_KEY = os.getenv('DEEPL_API_KEY')

SUPABASE_PB_KEY = os.getenv('SUPABASE_ANON_PUBLIC_KEY')
SUPABASE_URL = os.getenv('SUPABASE_PROJECT_URL')
SUPABASE_TABLE = 'speech-therapy-s3-keys'
SCOREBOARD_TABLE = 'scoreboard'

AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')

app = Flask(__name__)
app.secret_key = os.urandom(24) 

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

def supabase_request(method, table, data=None, query_params=None):
    """
    Generic function to interact with Supabase.
    
    Args:
        method: HTTP method (GET, POST, PATCH, etc.)
        table: Supabase table name
        data: Data to send (for POST, PATCH)
        query_params: Query parameters to append to URL
        
    Returns:
        Response from Supabase API
    """
    headers = {
        "apikey": SUPABASE_PB_KEY,
        "Authorization": f"Bearer {SUPABASE_PB_KEY}",
        "Content-Type": "application/json"
    }
    
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    if query_params:
        url += f"?{query_params}"
    
    if method == 'GET':
        return requests.get(url, headers=headers)
    elif method == 'POST':
        return requests.post(url, headers=headers, json=data)
    elif method == 'PATCH':
        return requests.patch(url, headers=headers, json=data)

def save_to_supabase(s3_key, word, translation): 
    data = {
        's3_key': s3_key, 
        "eng_word": word,
        "tr_word": translation  
    }
    
    return supabase_request('POST', SUPABASE_TABLE, data=data)

def update_scoreboard(username, action):
    """
    Update the scoreboard in Supabase for a user.
    Action should be either 'accepted' or 'rejected'.
    """
    # First check if the user exists
    response = supabase_request('GET', SCOREBOARD_TABLE, 
                               query_params=f"username=eq.{username}&select=*")
    
    if response.status_code == 200 and response.json():
        # User exists, update the relevant column
        user_data = response.json()[0]
        update_data = {
            action: user_data.get(action, 0) + 1
        }
        
        return supabase_request('PATCH', SCOREBOARD_TABLE, 
                               data=update_data,
                               query_params=f"username=eq.{username}")
    else:
        # User doesn't exist, create a new entry
        new_user = {
            "username": username,
            "accepted": 1 if action == "accepted" else 0,
            "rejected": 1 if action == "rejected" else 0
        }
        
        return supabase_request('POST', SCOREBOARD_TABLE, data=new_user)

def get_scoreboard():
    """
    Fetch scoreboard data from Supabase, calculate totals, and sort by total.
    """
    response = supabase_request('GET', SCOREBOARD_TABLE, query_params="select=*")
    
    if response.status_code == 200:
        users = response.json()
        
        # Calculate total for each user
        for user in users:
            user['total'] = user.get('accepted', 0) + user.get('rejected', 0)
        
        # Sort by total in descending order
        users.sort(key=lambda x: x['total'], reverse=True)
        
        return users
    else:
        # Return empty list if there was an error
        return []

@app.route('/username', methods=['GET', 'POST'])
def set_username():
    if request.method == 'POST':
        username = request.form['username']
        if username.strip():  # Ensure username isn't empty
            session['username'] = username
            return redirect(url_for('home'))
    return render_template('username.html')

def upload_to_s3(image_url, translation):
    img_data = requests.get(image_url).content
    unique_id = uuid.uuid4()
    
    ext = 'jpeg' if 'pexels' in image_url or 'unsplash' in image_url else 'jpg'
    s3_key = f'{translation}-{unique_id}.{ext}'

    s3 = boto3.client('s3',
                      aws_access_key_id=AWS_ACCESS_KEY,
                      aws_secret_access_key=AWS_SECRET_ACCESS_KEY)

    s3.put_object(Bucket='therapy-app-s3', Key=s3_key, Body=img_data, ContentType='image/jpeg')
    return s3_key

@app.route('/')
def home():
    # Check if user has set a username
    if 'username' not in session:
        return redirect(url_for('set_username'))
    
    word = random.choice(WORD_LIST).title()
    
    image_providers = [get_pexels_image, get_unsplash_image, get_pixabay_image]
    
    for provider_func in image_providers:
        image_url = provider_func(word)
        if image_url: 
            break

    translation = translate_deepl(word).title()
    
    # Get scoreboard data
    scoreboard = get_scoreboard()
    
    return render_template('index.html', 
                          word=word, 
                          image_url=image_url, 
                          translation=translation, 
                          username=session['username'],
                          scoreboard=scoreboard)

@app.route('/upload', methods=['POST'])
def upload():
    if 'username' not in session:
        return redirect(url_for('set_username'))
    
    image_url = request.form['image_url']
    word = request.form['word']
    translation = request.form['translation']

    s3_key = upload_to_s3(image_url, translation)
    save_to_supabase(s3_key, word, translation)
    
    # Update scoreboard - user accepted an image
    update_scoreboard(session['username'], 'accepted')

    return redirect(url_for('home'))

@app.route('/reject', methods=['POST'])
def reject():
    if 'username' not in session:
        return redirect(url_for('set_username'))
    
    # Update scoreboard - user rejected an image
    update_scoreboard(session['username'], 'rejected')
    
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)