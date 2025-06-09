from google.cloud import translate_v2 as translate_client
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set the path to the Google Cloud service account JSON file
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'google_stt.json'

def translate_text(text, source="en", target="tr"):
    """
    Translates text using Google Cloud Translation API.
    
    Args:
        text (str): The text to translate
        source (str): Source language code (e.g., 'en' for English)
        target (str): Target language code (e.g., 'tr' for Turkish)
    
    Returns:
        str: The translated text
    """
    try:
        # Initialize the Translation client
        client = translate_client.Client()
        
        # Perform the translation
        result = client.translate(
            text,
            source_language=source,
            target_language=target
        )
        
        # Debug: print the response to understand the structure
        print(f"Google Cloud Translation API response: {result}")
        
        return result['translatedText']
        
    except Exception as e:
        raise Exception(f"Translation failed: {e}")

# Keep the old function name for backward compatibility
def translate(text, source="EN", target="TR"):
    """
    Legacy function for backward compatibility.
    Converts language codes to lowercase and calls translate_text.
    """
    return translate_text(text, source.lower(), target.lower())
