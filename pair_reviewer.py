import requests
import os
import boto3
from flask import Flask, render_template, redirect, url_for, request, jsonify
from database import (
    supabase_request,
    SUPABASE_PB_KEY,
    SUPABASE_URL,
    AWS_ACCESS_KEY,
    AWS_SECRET_ACCESS_KEY
)

# Table for review
REVIEW_TABLE = 'speech-therapy-s3-keys'
S3_BUCKET = 'therapy-app-s3'
AWS_REGION = 'eu-north-1'
app = Flask(__name__)

def update_confirmation(s3_key, is_confirmed):
    """Set is_confirmed to true or false for a record"""
    headers = {
        "apikey": SUPABASE_PB_KEY,
        "Authorization": f"Bearer {SUPABASE_PB_KEY}",
        "Content-Type": "application/json"
    }
    
    url = f"{SUPABASE_URL}/rest/v1/{REVIEW_TABLE}?s3_key=eq.{s3_key}"
    response = requests.patch(url, headers=headers, json={"is_confirmed": is_confirmed})
    return response.status_code in (200, 204)

def get_records(limit=20, offset=0):
    """Get paginated records from Supabase, only unreviewed"""
    # Add filter: is_confirmed is null
    query_params = f"select=*&is_confirmed=is.null&limit={limit}&offset={offset}"
    response = supabase_request('GET', REVIEW_TABLE, query_params=query_params)
    if response.status_code == 200:
        return response.json()
    return []

def get_image_url(s3_key):
    """Generate a presigned URL for an S3 object"""
    s3 = boto3.client(
        's3',
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )
    
    url = s3.generate_presigned_url(
        'get_object',
        Params={'Bucket': S3_BUCKET, 'Key': s3_key},
        ExpiresIn=3600
    )
    
    return url

@app.route('/')
def index():
    page = int(request.args.get('page', 1))
    per_page = 20
    offset = (page - 1) * per_page
    records = get_records(limit=per_page, offset=offset)
    # Add S3 URLs to records
    for record in records:
        if record.get('s3_key'):
            try:
                record['image_url'] = get_image_url(record['s3_key'])
            except Exception as e:
                print(f"Error generating URL for {record['s3_key']}: {e}")
                record['image_url'] = None
    return render_template('reviewer.html', records=records, page=page)

@app.route('/confirm/<s3_key>', methods=['GET', 'POST'])
def confirm(s3_key):
    page = request.args.get('page', 1)
    is_ajax = request.args.get('ajax')
    success = update_confirmation(s3_key, True)
    if is_ajax:
        return ('', 200) if success else ('', 400)
    if success:
        return redirect(url_for('index', page=page))
    else:
        return f"Error confirming record"

@app.route('/deny/<s3_key>', methods=['GET', 'POST'])
def deny(s3_key):
    page = request.args.get('page', 1)
    is_ajax = request.args.get('ajax')
    success = update_confirmation(s3_key, False)
    if is_ajax:
        return ('', 200) if success else ('', 400)
    if success:
        return redirect(url_for('index', page=page))
    else:
        return f"Error denying record"

if __name__ == "__main__":
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    # Create the HTML template file
    with open('templates/reviewer.html', 'w') as f:
        f.write('''
<!DOCTYPE html>
<html>
<head>
    <title>Image-Word Pair Reviewer</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .grid-container {
            display: grid;
            grid-template-columns: repeat(3, 1fr); /* 3 columns */
            gap: 20px;
        }
        .image-card { border: 1px solid #ddd; padding: 15px; border-radius: 5px; background: #fff; }
        .image-container { max-width: 300px; margin: 10px 0; }
        img { max-width: 100%; height: auto; }
        .button-container { display: flex; gap: 10px; }
        .confirm-btn { background: #4CAF50; color: white; border: none; padding: 8px 15px; border-radius: 4px; cursor: pointer; }
        .deny-btn { background: #ff9800; color: white; border: none; padding: 8px 15px; border-radius: 4px; cursor: pointer; }
        .confirmed { background-color: #e6ffe6; border-color: #4CAF50; }
        .denied { background-color: #fff0e6; border-color: #ff9800; }
    </style>
</head>
<body>
    <h1>Image-Word Pair Reviewer</h1>
    
    {% if records %}
        <p>Found {{ records|length }} records to review.</p>
        
        <div class="grid-container">
        {% for record in records %}
            <div class="image-card {% if record.get('is_confirmed') == true %}confirmed{% elif record.get('is_confirmed') == false %}denied{% endif %}">
                <h3>Word: {{ record.get('tr_word', 'N/A') }}</h3>
                <p>Confirmed: {{ record.get('is_confirmed', 'Not set') }}</p>
                <p>S3 Key: {{ record.get('s3_key', 'N/A') }}</p>
                
                <div class="image-container">
                    {% if record.get('image_url') %}
                        <img src="{{ record.get('image_url') }}" alt="{{ record.get('tr_word', 'Image') }}">
                    {% else %}
                        <p>No image URL available</p>
                    {% endif %}
                </div>
                
                <div class="button-container">
                    {% if record.get('is_confirmed') != true %}
                    <button class="confirm-btn" onclick="confirmPair('{{ record.get('s3_key', '') }}', this)">Confirm Pair</button>
                    {% endif %}
                    
                    {% if record.get('is_confirmed') != false %}
                    <button class="deny-btn" onclick="denyPair('{{ record.get('s3_key', '') }}', this)">Deny Pair</button>
                    {% endif %}
                </div>
            </div>
        {% endfor %}
        </div>
        
        <div style="margin-top: 20px;">
            {% if page > 1 %}
                <a href="{{ url_for('index', page=page-1) }}">Previous</a>
            {% endif %}
            <span>Page {{ page }}</span>
            {% if records|length == 20 %}
                <a href="{{ url_for('index', page=page+1) }}">Next</a>
            {% endif %}
        </div>
    {% else %}
        <p>No records found.</p>
    {% endif %}
    
    <script>
    function updateCardStatus(button, status) {
        const card = button.closest('.image-card');
        card.classList.remove('confirmed', 'denied');
        if (status === true) {
            card.classList.add('confirmed');
            card.querySelector('.confirm-btn').style.display = 'none';
            if (card.querySelector('.deny-btn')) card.querySelector('.deny-btn').style.display = 'inline-block';
            card.querySelector('p:nth-child(2)').innerText = 'Confirmed: true';
        } else if (status === false) {
            card.classList.add('denied');
            card.querySelector('.deny-btn').style.display = 'none';
            if (card.querySelector('.confirm-btn')) card.querySelector('.confirm-btn').style.display = 'inline-block';
            card.querySelector('p:nth-child(2)').innerText = 'Confirmed: false';
        }
    }

    function confirmPair(s3_key, button) {
        fetch(`/confirm/${s3_key}?ajax=1`, { method: 'POST' })
            .then(res => res.ok ? updateCardStatus(button, true) : alert('Error confirming'))
    }

    function denyPair(s3_key, button) {
        fetch(`/deny/${s3_key}?ajax=1`, { method: 'POST' })
            .then(res => res.ok ? updateCardStatus(button, false) : alert('Error denying'))
    }
    </script>
</body>
</html>
        ''')
    
    app.run(debug=True)