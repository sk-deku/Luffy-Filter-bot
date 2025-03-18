import os
import requests

MODIJI_API_KEY = os.getenv("MODIJI_API_KEY", "")
MODIJI_URL = "https://modijiurl.com/api"

def shorten_url(long_url):
    """
    Shortens a given URL using ModijiURL API.
    """
    try:
        response = requests.post(
            MODIJI_URL,
            json={"url": long_url, "api_key": MODIJI_API_KEY}
        )
        data = response.json()

        if response.status_code == 200 and "shortened_url" in data:
            return data["shortened_url"]
        else:
            return None
    except requests.exceptions.RequestException as e:
        print(f"Shortener API error: {e}")
        return None
