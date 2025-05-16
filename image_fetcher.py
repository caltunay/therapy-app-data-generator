import requests
import os

BRAVE_API_KEY = os.getenv('BRAVE_API_KEY')
UNSPLASH_ACCESS_KEY = os.getenv('UNSPLASH_API_KEY')
PIXABAY_API_KEY = os.getenv('PIXABAY_API_KEY')
PEXELS_API_KEY = os.getenv('PEXELS_API_KEY')

def get_brave_image(word):
    """
    Fetch the most relevant image from Brave Search.
    
    Args:
        word (str): Search term
        
    Returns:
        str: URL of the most relevant image
    """
    url = 'https://api.search.brave.com/res/v1/images/search'

    headers = {
        'Accept': 'application/json',
        'X-Subscription-Token': BRAVE_API_KEY,
    }

    params = {
        'q': f"{word} photograph",
        'count': 1,  # number of images
    }
    
    response = requests.get(url, headers=headers, params=params)
    # print(response.status_code)
    if response.status_code == 200:# and len(data['results']) > 0:
        data = response.json()
        return data['results'][0]['properties']['url']
    return None

def get_pexels_image(word, orientation=None, color=None, max_results=10):
    """
    Fetch images from Pexels with improved relevance.
    
    Args:
        word (str): Search term
        orientation (str, optional): 'landscape', 'portrait', or 'square'
        color (str, optional): Color to filter by (e.g., 'red', 'blue')
        max_results (int, optional): Maximum number of results to consider
        
    Returns:
        str: URL of the most relevant image
    """
    headers = {'Authorization': PEXELS_API_KEY}
    params = {
        'query': word,
        'per_page': max_results,
        'size': 'medium'  # Prefer medium-sized images for better quality
    }
    
    # Add optional filters
    if orientation in ['landscape', 'portrait', 'square']:
        params['orientation'] = orientation
    
    if color:
        params['color'] = color
        
    response = requests.get('https://api.pexels.com/v1/search', headers=headers, params=params)
    data = response.json()
    
    if not data.get('photos'):
        return None
        
    photos = data['photos']
    
    if not photos:
        return None
        
    # If we have multiple results, try to find the most relevant one
    if len(photos) > 1:
        # Score images based on relevance factors
        scored_photos = []
        
        for photo in photos:
            score = 0
            
            # Images with the search term in their title/description are more relevant
            if word.lower() in photo.get('alt', '').lower():
                score += 5
                
            # Photographer-selected images might be higher quality
            if photo.get('photographer'):
                score += 1
                
            # Prefer images with higher width/quality
            score += min(photo.get('width', 0) / 1000, 3)
            
            scored_photos.append((score, photo))
            
        # Sort by score (highest first)
        scored_photos.sort(reverse=True, key=lambda x: x[0])
        best_photo = scored_photos[0][1]
        
        return best_photo['src']['original']
    else:
        # If only one result, return it
        return photos[0]['src']['original']

def get_unsplash_image(word, orientation=None, color=None, max_results=30):
    """
    Fetch the most relevant image from Unsplash.
    
    Args:
        word (str): Search term
        orientation (str, optional): 'landscape', 'portrait', or 'square'
        color (str, optional): Color filter (e.g., 'black', 'blue')
        max_results (int, optional): Maximum number of results to consider
        
    Returns:
        str: URL of the most relevant image
    """
    params = {
        'query': word,
        'per_page': max_results,
        'client_id': UNSPLASH_ACCESS_KEY,
        'order_by': 'relevant',  # Focus on relevance first
        'content_filter': 'high'  # Filter for high-quality content
    }
    
    # Add optional filters
    if orientation in ['landscape', 'portrait', 'square']:
        params['orientation'] = orientation
    
    if color:
        params['color'] = color
    
    r = requests.get("https://api.unsplash.com/search/photos", params=params)
    if r.status_code != 200:
        return None
    
    data = r.json()
    results = data.get('results', [])
    
    if not results:
        return None
    
    # Score images based on relevance criteria
    scored_results = []
    for img in results:
        score = 0
        
        # Check if search term appears in description or alt text - safely handle None values
        description = img.get('description', '') or ''
        if description:  # Only call lower() if description exists and is not None
            description = description.lower()
            
        alt = img.get('alt_description', '') or ''
        if alt:  # Only call lower() if alt exists and is not None
            alt = alt.lower()
            
        if word.lower() in description or word.lower() in alt:
            score += 10
        
        # Higher likes/downloads suggest better quality/relevance
        score += min(img.get('likes', 0) / 50, 5)  # Cap at 5 points
        
        # Better resolution images may be more useful
        width = img.get('width', 0)
        height = img.get('height', 0)
        score += min((width * height) / 1000000, 3)  # Cap at 3 points
        
        # Check for tags that match the query
        tags = img.get('tags', [])
        for tag in tags:
            tag_title = tag.get('title', '') or ''
            if tag_title and word.lower() in tag_title.lower():
                score += 5
                break
        
        scored_results.append((score, img))
    
    # Sort by score (highest first)
    scored_results.sort(reverse=True, key=lambda x: x[0])
    
    # Return the URL of the highest-scoring image (regular size for better quality than small)
    return scored_results[0][1]['urls']['regular'] if scored_results else None

def get_pixabay_image(word, orientation=None, color=None, max_results=30):
    """
    Fetch the most relevant image from Pixabay.
    
    Args:
        word (str): Search term
        orientation (str, optional): 'landscape', 'portrait'
        color (str, optional): Color filter (e.g., 'red', 'blue')
        max_results (int, optional): Maximum number of results to consider
        
    Returns:
        str: URL of the most relevant image
    """
    params = {
        'key': PIXABAY_API_KEY,
        'q': word,
        'image_type': 'photo',
        'per_page': max_results,
        'safesearch': True
    }
    
    # Add optional filters
    if orientation == 'landscape':
        params['orientation'] = 'horizontal'
    elif orientation == 'portrait':
        params['orientation'] = 'vertical'
    
    if color:
        params['colors'] = color
    
    response = requests.get("https://pixabay.com/api/", params=params)
    if response.status_code != 200:
        return None
    
    data = response.json()
    hits = data.get('hits', [])
    
    if not hits:
        return None
    
    # Score images based on relevance criteria
    scored_hits = []
    word_lower = word.lower()
    
    for img in hits:
        score = 0
        
        # Check if tags match the search term
        tags = img.get('tags', '').lower()
        if word_lower in tags:
            score += 10
        
        # Higher popularity metrics suggest better quality/relevance
        score += min(img.get('views', 0) / 1000, 5)  # Cap at 5 points
        score += min(img.get('downloads', 0) / 200, 5)  # Cap at 5 points
        score += min(img.get('likes', 0) / 100, 3)  # Cap at 3 points
        
        # Better resolution images may be more useful
        resolution = img.get('imageWidth', 0) * img.get('imageHeight', 0)
        score += min(resolution / 1000000, 3)  # Cap at 3 points
        
        scored_hits.append((score, img))
    
    # Sort by score (highest first)
    scored_hits.sort(reverse=True, key=lambda x: x[0])
    
    # Return the URL of the highest-scoring image
    return scored_hits[0][1]['largeImageURL'] if scored_hits else None


