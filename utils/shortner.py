import requests
import os

MODIJI_API_KEY = os.getenv("MODIJI_API_KEY")
MODIJI_API_URL = "https://modijiurl.com/api"

def shorten_url(long_url):
    if not MODIJI_API_KEY:
        return None
    
    try:
        response = requests.post(
            MODIJI_API_URL,
            json={"url": long_url, "api_key": MODIJI_API_KEY},
            timeout=5
        )
        
        if response.status_code == 200:  # Ensure the response is successful
            try:
                data = response.json()
                return data.get("shortenedUrl")
            except ValueError:  # Handles JSON decoding error
                print("Shortener API returned invalid JSON")
                return None
        else:
            print(f"Shortener API error: HTTP {response.status_code}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Shortener API error: {e}")
        return None
