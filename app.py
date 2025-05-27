from flask import Flask, render_template, request, redirect, url_for, session
import os
from dotenv import load_dotenv
import random

from image_fetcher import get_brave_image, get_pexels_image, get_unsplash_image, get_pixabay_image
from translation import translate_deepl
from database import (
    save_to_supabase, update_scoreboard, get_scoreboard, upload_to_s3,
    get_unused_word, mark_word_as_used
)

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24) 

@app.route('/username', methods=['GET', 'POST'])
def set_username():
    if request.method == 'POST':
        username = request.form['username']
        if username.strip():  # Ensure username isn't empty
            session['username'] = username
            return redirect(url_for('home'))
    return render_template('username.html')

@app.route('/')
def home():
    # Check if user has set a username
    if 'username' not in session:
        return redirect(url_for('set_username'))
    
    word = get_unused_word()
    if not word:
        return "No unused words available.", 404
    print(word)

    word = word.title()
    image_providers = [get_unsplash_image, get_brave_image, get_pexels_image, get_pixabay_image] 
    
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
    mark_word_as_used(word)
    
    # Update scoreboard - user accepted an image
    update_scoreboard(session['username'], 'accepted')

    return redirect(url_for('home'))

@app.route('/reject', methods=['POST'])
def reject():
    if 'username' not in session:
        return redirect(url_for('set_username'))
    
    # Update scoreboard - user rejected an image
    update_scoreboard(session['username'], 'rejected')
    # update by cenan
    word = request.form['word']
    mark_word_as_used(word)
    # end of update 
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)