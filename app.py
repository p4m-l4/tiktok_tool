from flask import Flask, request, jsonify
import requests
import openai
from bs4 import BeautifulSoup
import os

# Load environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINTEREST_ACCESS_TOKEN = os.getenv("PINTEREST_ACCESS_TOKEN")
PINTEREST_BOARD_ID = os.getenv("PINTEREST_BOARD_ID")

# Configure APIs
openai.api_key = OPENAI_API_KEY

app = Flask(__name__)

@app.route('/')
def home():
    return "Welcome to the Amazon-TikTok-Pinterest app! Use the /process endpoint for API requests with a POST request."

@app.route('/process', methods=['POST'])
def process_input():
    data = request.json
    product_name = data.get('product_name')
    affiliate_link = data.get('affiliate_link')

    if not product_name or not affiliate_link:
        return jsonify({"error": "Both product_name and affiliate_link are required."}), 400

    # Step 1: Search TikTok for relevant videos
    tiktok_videos = search_tiktok_videos(product_name)
    if not tiktok_videos:
        return jsonify({"error": "No suitable TikTok videos found."}), 404

    # Step 2: Generate a catchy phrase using OpenAI
    catchy_phrase = generate_catchy_phrase(product_name)

    # Step 3: Create a Pinterest pin
    pin_url = create_pinterest_pin(product_name, catchy_phrase, affiliate_link)
    if not pin_url:
        return jsonify({"error": "Failed to create Pinterest pin."}), 500

    return jsonify({
        "product_name": product_name,
        "affiliate_link": affiliate_link,
        "tiktok_videos": tiktok_videos,
        "catchy_phrase": catchy_phrase,
        "pinterest_pin": pin_url
    })

def search_tiktok_videos(product_name):
    try:
        search_url = f"https://www.tiktok.com/search?q={product_name.replace(' ', '%20')}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(search_url, headers=headers)
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, 'html.parser')
        videos = []
        for link in soup.find_all('a', href=True):
            if "/video/" in link['href']:
                videos.append(f"https://www.tiktok.com{link['href']}")
            if len(videos) == 5:
                break

        return videos if videos else None

    except Exception as e:
        print(f"Error searching TikTok: {e}")
        return None

def generate_catchy_phrase(product_name):
    try:
        prompt = f"Write a catchy and consumer-friendly phrase for a product named '{product_name}'."
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=20
        )
        return response.choices[0].text.strip()
    except Exception as e:
        print(f"Error generating catchy phrase: {e}")
        return "Your perfect choice!"

def create_pinterest_pin(product_name, description, affiliate_link):
    try:
        url = "https://api.pinterest.com/v1/pins/"
        headers = {
            "Authorization": f"Bearer {PINTEREST_ACCESS_TOKEN}"
        }
        data = {
            "board": PINTEREST_BOARD_ID,
            "note": f"{description}\n{affiliate_link}",
            "link": affiliate_link,
            "image_url": "https://via.placeholder.com/500"  # Replace with actual product image if available
        }
        response = requests.post(url, headers=headers, json=data)

        if response.status_code == 201:
            return response.json().get('url')
        else:
            print(f"Pinterest API error: {response.text}")
            return None

    except Exception as e:
        print(f"Error creating Pinterest pin: {e}")
        return None

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
