# Flask Word App

This project is a Flask web application that randomly selects a word, fetches an image from Unsplash, translates the word to Turkish using DeepL, and allows users to either upload the image to Imgur or reject it for a new word and image.

## Project Structure

```
flask-word-app
├── app.py               # Main application file
├── templates
│   └── index.html      # HTML structure for the web application
├── static
│   └── styles.css      # CSS styles for the web application
├── requirements.txt     # List of dependencies
├── .env                 # Environment variables (API keys)
└── README.md            # Project documentation
```

## Setup Instructions

1. **Clone the repository**:
   ```
   git clone <repository-url>
   cd flask-word-app
   ```

2. **Create a virtual environment**:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install the required packages**:
   ```
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   Create a `.env` file in the root directory and add your Unsplash and DeepL API keys:
   ```
   unsplash_api_key=YOUR_UNSPLASH_API_KEY
   deepl_api_key=YOUR_DEEPL_API_KEY
   imgur_client_id=YOUR_IMGUR_CLIENT_ID
   ```

## Usage

1. **Run the application**:
   ```
   python app.py
   ```

2. **Access the application**:
   Open your web browser and go to `http://127.0.0.1:5000/`.

3. **Interacting with the application**:
   - A random word and its corresponding image will be displayed.
   - Click the "Upload" button to upload the image to Imgur and save the URL and Turkish translation to `app_data.csv`.
   - Click the "Reject" button to fetch a new random word and image.

## Dependencies

- Flask
- requests
- python-dotenv
- (Any other necessary libraries)

## License

This project is licensed under the MIT License.