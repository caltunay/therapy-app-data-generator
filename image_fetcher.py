\
import requests
import os

UNSPLASH_ACCESS_KEY = os.getenv('UNSPLASH_API_KEY')
PIXABAY_API_KEY = os.getenv('PIXABAY_API_KEY')
PEXELS_API_KEY = os.getenv('PEXELS_API_KEY')

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
