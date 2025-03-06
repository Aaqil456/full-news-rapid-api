import os
import requests
import json
import time
import base64
from datetime import datetime


# Environment Variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")
WP_URL = os.getenv("WP_URL", "https://teknologiblockchain.com/wp-json/wp/v2")
WP_USER = os.getenv("WP_USER")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD")

NEWS_CATEGORY_ID = 1413


def translate_text_gemini(text):
    if not text or not isinstance(text, str) or not text.strip():
        return "Translation failed"

    gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": f"Translate this text '{text}' into Malay. Only return the translated text, structured like an article. Please exclude or don't take any sentences that looks like an advertisement from the text"}]}]
    }

    for attempt in range(5):
        try:
            response = requests.post(gemini_url, headers=headers, json=payload)
            if response.status_code == 200:
                data = response.json()
                translated = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                return translated.strip() if translated else "Translation failed"
            elif response.status_code == 429:
                print(f"[Rate Limit] Retrying in {2 ** attempt} seconds...")
                time.sleep(2 ** attempt)
            else:
                print(f"[Gemini Error] {response.status_code}: {response.text}")
                return "Translation failed"
        except Exception as e:
            print(f"[Gemini Exception] {e}")
            return "Translation failed"
    return "Translation failed"


def fetch_news_from_apify():
    url = f"https://api.apify.com/v2/acts/buseta~crypto-news/run-sync-get-dataset-items?token={APIFY_API_TOKEN}"
    try:
        response = requests.post(url, timeout=600)
        if response.status_code == 201:
            return response.json()
        else:
            print(f"[Apify Error] {response.status_code}: {response.text}")
            return []
    except Exception as e:
        print(f"[Apify Exception] {e}")
        return []


def upload_image_to_wordpress(image_url):
    if not image_url:
        print("[SKIP] No image URL provided.")
        return None, None

    try:
        response = requests.get(image_url)
        if response.status_code != 200:
            print(f"[Image Download Error] {response.status_code}: Unable to fetch image.")
            return None, None
        image_data = response.content
    except Exception as e:
        print(f"[Image Download Exception] {e}")
        return None, None

    media_endpoint = f"{WP_URL}/media"
    credentials = f"{WP_USER}:{WP_APP_PASSWORD}"
    token = base64.b64encode(credentials.encode()).decode()

    file_name = image_url.split("/")[-1]
    headers = {
        "Authorization": f"Basic {token}",
        "Content-Disposition": f"attachment; filename={file_name}",
        "Content-Type": "image/jpeg",
    }

    response = requests.post(media_endpoint, headers=headers, data=image_data)
    if response.status_code == 201:
        media_data = response.json()
        media_id = media_data.get("id")
        media_url = media_data.get("source_url")
        print(f"[Image Uploaded] Media ID: {media_id}")
        return media_id, media_url
    else:
        print(f"[Image Upload Error] {response.status_code}: {response.text}")
        return None, None


def post_to_wordpress(title, content, original_url, image_url, media_id=None, status="publish"):
    credentials = f"{WP_USER}:{WP_APP_PASSWORD}"
    token = base64.b64encode(credentials.encode()).decode()
    post_endpoint = f"{WP_URL}/posts"

    image_html = f'<img src="{image_url}" alt="{title}"/>' if image_url else ""

    full_content = f'''
<h1>{title}</h1>

{image_html}

{content}

<p>📌 Baca artikel asal di sini: <a href="{original_url}" target="_blank" rel="noopener noreferrer">{original_url}</a></p>
'''

    post_data = {
        "title": title,
        "content": full_content,
        "status": status,
        "categories": [NEWS_CATEGORY_ID]
    }
    if media_id:
        post_data["featured_media"] = media_id

    headers = {
        "Authorization": f"Basic {token}",
        "Content-Type": "application/json",
    }

    response = requests.post(post_endpoint, headers=headers, json=post_data)
    if response.status_code == 201:
        print(f"[Post Created] {title}")
        return True
    else:
        print(f"[Post Error] {response.status_code}: {response.text}")
        return False


def save_to_json(news_list, filename="translated_news.json"):
    output = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "all_news": news_list
    }
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=4)
    print(f"[JSON Saved] {filename}")


def main():
    if not APIFY_API_TOKEN or not GEMINI_API_KEY or not WP_USER or not WP_APP_PASSWORD:
        print("[ERROR] One or more environment variables are missing!")
        return

    fetched_news = fetch_news_from_apify()
    translated_news = []

    for idx, news in enumerate(fetched_news[:20]):
        source = news.get("source", "")

        if source != "Cointelegraph.com News":
            print(f"[SKIP] Source is '{source}'. Only processing Cointelegraph.com News.")
            continue

        print(f"\nProcessing news {idx + 1} of {min(20, len(fetched_news))}")

        original_url = news.get("link") or ""
        image_url = news.get("image") or ""

        if not original_url:
            print(f"[SKIP] No original URL found. Skipping this news.")
            continue

        title = translate_text_gemini(news.get("title") or "")
        description = translate_text_gemini(news.get("summary") or "")
        content = translate_text_gemini(news.get("content") or "")

        if title == "Translation failed" or content == "Translation failed":
            print(f"[SKIP] Translation failed for '{news.get('title', 'Untitled')}'. Skipping this news.")
            continue

        media_id, uploaded_image_url = upload_image_to_wordpress(image_url)

        image_in_post_url = uploaded_image_url if uploaded_image_url else None

        post_success = post_to_wordpress(title, content, original_url, image_in_post_url, media_id)

        translated_news.append({
            "title": title,
            "description": description,
            "content": content,
            "image": uploaded_image_url,
            "url": original_url,
            "source": source,
            "timestamp": news.get("time", datetime.now().isoformat()),
            "status": "Posted" if post_success else "Failed"
        })

        time.sleep(1)

    save_to_json(translated_news)


if __name__ == "__main__":
    main()
