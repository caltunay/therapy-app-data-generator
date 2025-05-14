import requests
import boto3
import os
import uuid
from io import BytesIO
from PIL import Image

SUPABASE_PB_KEY = os.getenv('SUPABASE_ANON_PUBLIC_KEY')
SUPABASE_URL = os.getenv('SUPABASE_PROJECT_URL')
SUPABASE_TABLE = 'speech-therapy-s3-keys'
SCOREBOARD_TABLE = 'scoreboard'

AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')

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

def upload_to_s3(image_url, translation):
    img_data = requests.get(image_url).content
    unique_id = uuid.uuid4()
    
    # Resize image before uploading
    img = Image.open(BytesIO(img_data))
    max_size = 800  # Maximum dimension in pixels
    img.thumbnail((max_size, max_size))
    
    # Save optimized image to buffer
    buffer = BytesIO()
    img.save(buffer, format="JPEG", quality=85, optimize=True)
    buffer.seek(0)
    
    s3_key = f'{translation}-{unique_id}.jpeg'
    
    s3 = boto3.client('s3',
                     aws_access_key_id=AWS_ACCESS_KEY,
                     aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
    
    s3.put_object(Bucket='therapy-app-s3', Key=s3_key, Body=buffer, ContentType='image/jpeg')
    return s3_key
