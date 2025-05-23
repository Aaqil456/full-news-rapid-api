import os
import requests
import json
import time
import base64
from datetime import datetime
from urllib.parse import urlparse

# === ENV VARIABLES ===
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
WP_URL = os.getenv("WP_URL", "https://teknologiblockchain.com/wp-json/wp/v2")
WP_USER = os.getenv("WP_USER")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD")
FB_PAGE_ACCESS_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN")
FB_PAGE_ID = os.getenv("FB_PAGE_ID")

NEWS_CATEGORY_ID = 1413  # WordPress category

ALLOWED_NEWS_DOMAINS = [
    "coindesk.com",
    "cointelegraph.com",
    "bitcoinist.com",
    "decrypt.co",
    "cryptodaily.co.uk",
    "bitcoinethereumnews.com"
    
]

# === MAIN FUNCTION ===
ALLOWED_FB_SOURCES = [
    "coindesk.com",
    "cointelegraph.com",
    "bitcoinist.com",
    "decrypt.co",
    "cryptodaily.co.uk"
]

# === FETCH NEWS ===
def extract_domain(link):
    try:
        netloc = urlparse(link).netloc.lower()
        return netloc.replace("www.", "")
    except:
        return ""

def fetch_news():
    url = "https://crypto-news51.p.rapidapi.com/api/v1/crypto/articles"
    querystring = {"page": "1", "limit": "10", "time_frame": "24h", "format": "json"}
    headers = {
        "x-rapidapi-key": os.getenv("RAPIDAPI_KEY"),
        "x-rapidapi-host": "crypto-news51.p.rapidapi.com"
    }

    try:
        response = requests.get(url, headers=headers, params=querystring, timeout=10)
        if response.status_code != 200:
            print(f"[RapidAPI Error] {response.status_code}: {response.text}")
            return []

        raw_data = response.json()
        posted_links = get_already_posted_links()
        filtered_news = []

        for article in raw_data:
            link = article.get("link", "")
            if not link or link in posted_links:
                continue

            domain = extract_domain(link)
            if domain not in ALLOWED_NEWS_DOMAINS:
                print(f"[Filtered] Not allowed domain: {domain}")
                continue
                
            sentiment = article.get("sentiment", {}).get("label", "unknown")
            image_url = article.get("media", [""])[0] if article.get("media") else ""
            source = domain  # Use domain as the "source"

            filtered_news.append({
                "title": article.get("title", ""),
                "summary": article.get("summary", ""),
                "content": article.get("summary", ""),  # use summary as content fallback
                "link": link,
                "image": image_url,
                "time": article.get("published", ""),
                "source": source,
                "sentiment": sentiment
            })

        return filtered_news

    except Exception as e:
        print(f"[RapidAPI Exception] {e}")
        return []

# === GEMINI TRANSLATION HELPERS ===
def query_gemini(prompt):
    if not prompt or not isinstance(prompt, str):
        return "Translation failed"

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    for attempt in range(5):
        try:
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                data = response.json()
                return data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()
            elif response.status_code == 429:
                print(f"[Rate Limit] Retry {attempt+1}...")
                time.sleep(2 ** attempt)
            else:
                print(f"[Gemini Error] {response.status_code}: {response.text}")
                break
        except Exception as e:
            print(f"[Gemini Exception] {e}")
            break
    return "Translation failed"


def translate_for_facebook(text):
    prompt = f"""
Translate the following news into Malay.  
Then, kindly write a short conclusion or summary of the news in less than 280 characters in 1 paragraph.  
Only return the short conclusion without any explanation, heading, or intro phrase.  
Use natural, conversational, friendly Malaysian Malay — like how a friend shares info.  
Keep it simple, relaxed, and easy to understand.  
Avoid using exaggerated slang words or interjections (such as "Eh," "Korang," "Woi," "Wooohooo," "Wooo," or anything similar).  
No shouting words or unnecessary excitement.  
Keep it informative, approachable, and casual — but clean and neutral.  
Do not use emojis unless they appear in the original text.  
Do not translate brand names or product names.  
Do not phrase the summary as if it is referring to a news source — write it as a general insight or observation instead.  
⚠️ Do NOT include phrases like "Terjemahan:", "Kesimpulan:", "Baiklah,", "Secara ringkas", "**Conclusion:**", "**Translation:**", or anything similar. Just give the final sentence.

Original news:
'{text}'
"""
    return query_gemini(prompt)


def translate_for_wordpress(text):
    prompt = f"""
        Translate the following article into Bahasa Melayu.
        
        ⚠️ Important instructions:
        - Do not add source credits like "tajuk asal..." or "muncul di..."
        - Do not include opening phrases like "Berikut adalah..."
        - Do not mention where the article was published.
        - Only return the clean translated article content, nothing more.
        - Maintain proper paragraph formatting.
        
        {text}
        """
    return query_gemini(prompt)


def translate_title(text):
    prompt = f"""
        Translate this **headline only** into Bahasa Melayu.
        Return only the translated headline, without explanation or formatting.
        
        {text}
        """
    return query_gemini(prompt)






# === IMAGE UPLOAD TO WORDPRESS ===
def upload_image_to_wp(image_url):
    if not image_url:
        print("[Upload Skipped] No image URL.")
        return None, None

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
            "Referer": "https://cointelegraph.com"  # Help bypass hotlinking blocks
        }
        img_response = requests.get(image_url, headers=headers)
        if img_response.status_code != 200:
            print(f"[Download Error] Status {img_response.status_code} for image: {image_url}")
            return None, None
        image_data = img_response.content
    except Exception as e:
        print(f"[Download Exception] {e}")
        return None, None

    # Setup WordPress credentials
    media_endpoint = f"{WP_URL}/media"
    credentials = f"{WP_USER}:{WP_APP_PASSWORD}"
    token = base64.b64encode(credentials.encode()).decode()

    # Filename from URL
    file_name = image_url.split("/")[-1] or "image.jpg"
    headers = {
        "Authorization": f"Basic {token}",
        "Content-Disposition": f"attachment; filename={file_name}",
        "Content-Type": "image/jpeg",  # You can dynamically detect MIME type later if needed
    }

    try:
        print(f"[Uploading] {file_name} to WP Media...")
        upload_response = requests.post(media_endpoint, headers=headers, data=image_data)
        if upload_response.status_code == 201:
            media_data = upload_response.json()
            print(f"[Upload Success] Media ID: {media_data.get('id')}")
            return media_data.get("id"), media_data.get("source_url")
        else:
            print(f"[Upload Error] Status {upload_response.status_code}: {upload_response.text}")
    except Exception as e:
        print(f"[Upload Exception] {e}")

    return None, None



# === POST TO WORDPRESS ===
def post_to_wp(title, content, original_url, uploaded_image_url=None, media_id=None, sentiment="unknown"):
    credentials = f"{WP_USER}:{WP_APP_PASSWORD}"
    token = base64.b64encode(credentials.encode()).decode()
    headers = {"Authorization": f"Basic {token}", "Content-Type": "application/json"}

    sentiment_html = f"<p><strong>Sentimen Artikel:</strong> {sentiment.capitalize()}</p>"
    image_html = f"<img src='{uploaded_image_url}' alt='{title}'/><br>" if uploaded_image_url else ""
    
    full_content = f"<h1>{title}</h1><br>{image_html}{content}{sentiment_html}<p>📌 Baca artikel asal di sini: <a href='{original_url}'>{original_url}</a></p>"


    post_data = {
        "title": title,
        "content": full_content,
        "status": "publish",
        "categories": [NEWS_CATEGORY_ID]
    }

    if media_id:
        post_data["featured_media"] = media_id
        time.sleep(2)

    try:
        response = requests.post(f"{WP_URL}/posts", headers=headers, json=post_data)
        if response.status_code == 201:
            print(f"[Post Created] {title}")
            return True
        else:
            print(f"[Post Error] {response.status_code}: {response.text}")
    except Exception as e:
        print(f"[Post WP Error] {e}")
    return False


# === POST TO FACEBOOK ===

# === DYNAMIC PAGE TOKEN HANDLER ===
def get_fresh_page_token():
    long_lived_user_token = os.getenv("LONG_LIVED_USER_TOKEN")
    if not long_lived_user_token:
        print("[FB] Missing LONG_LIVED_USER_TOKEN")
        return None

    try:
        response = requests.get(
            f"https://graph.facebook.com/v22.0/me/accounts?access_token={long_lived_user_token}"
        )
        data = response.json()
        if "data" in data and data["data"]:
            return data["data"][0]["access_token"]
        else:
            print("[FB] No pages found or invalid token.")
    except Exception as e:
        print(f"[FB] Error fetching page token: {e}")
    return None

def post_to_facebook(image_url, caption):
    page_token = get_fresh_page_token()
    if not page_token or not FB_PAGE_ID:
        print("[SKIP FB] Missing page token or page ID.")
        return False

    try:
        if image_url:
            data = {
                "url": image_url,
                "message": caption,
                "access_token": page_token
            }
            endpoint = f"https://graph.facebook.com/{FB_PAGE_ID}/photos"
        else:
            data = {
                "message": caption,
                "access_token": page_token
            }
            endpoint = f"https://graph.facebook.com/{FB_PAGE_ID}/feed"

        response = requests.post(endpoint, data=data)
        if response.status_code == 200:
            return True
        else:
            print(f"[FB ERROR] {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"[FB Post Exception] {e}")
        return False
    if not FB_PAGE_ACCESS_TOKEN or not FB_PAGE_ID:
        print("[SKIP FB] Missing config.")
        return False

    try:
        if image_url:
            data = {
                "url": image_url,
                "message": caption,
                "access_token": FB_PAGE_ACCESS_TOKEN
            }
            endpoint = f"https://graph.facebook.com/{FB_PAGE_ID}/photos"
        else:
            data = {
                "message": caption,
                "access_token": FB_PAGE_ACCESS_TOKEN
            }
            endpoint = f"https://graph.facebook.com/{FB_PAGE_ID}/feed"

        response = requests.post(endpoint, data=data)
        if response.status_code == 200:
            return True
        else:
            print(f"[FB ERROR] {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"[FB Post Exception] {e}")
        return False


# === SAVE JSON ===

def get_already_posted_links():
    try:
        with open("response.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            return {item.get("link") for item in data if item.get("link")}
    except Exception as e:
        print(f"[JSON Load Error] {e}")
        return set()

def update_response_json(new_items):
    try:
        with open("response.json", "r", encoding="utf-8") as f:
            existing = json.load(f)
    except:
        existing = []

    posted_links = {item.get("original_url") or item.get("link") for item in existing}

    combined = existing + [
        {
            "title": item["title"],
            "translated_title": item["translated_title"],
            "translated_summary": item["translated_summary"],
            "translated_content": item["translated_content"],
            "translated_facebook_post": item["translated_facebook_post"],
            "original_url": item["original_url"],
            "image": item["image"],
            "source": item["source"],
            "fb_status": item["fb_status"],
            "wp_status": item["wp_status"],
            "sentiment": item["sentiment"],
            "timestamp": item["timestamp"]
        }
        for item in new_items
        if item.get("original_url")
           and item.get("original_url") not in posted_links
           and (item.get("fb_status") == "Posted" or item.get("wp_status") == "Posted")
    ]

    with open("response.json", "w", encoding="utf-8") as f:
        json.dump(combined, f, ensure_ascii=False, indent=4)




def main():
    fetched_news = fetch_news()
    if not fetched_news:
        print("[NO NEWS]")
        return

    all_results = []

    for idx, news in enumerate(fetched_news[:20]):
        print(f"\n[{idx+1}] Processing: {news.get('title')}")

        source = news.get("source", "")
        title_raw = news.get("title", "")
        summary_raw = news.get("summary", "")
        content_raw = news.get("content", "")
        original_url = news.get("link", "")
        image_url = news.get("image", "")
        timestamp = news.get("time", datetime.now().isoformat())

        # === Facebook ===
        fb_caption = "Skipped"
        fb_status = "Skipped"
        if source in ALLOWED_FB_SOURCES:
            full_text = f"{title_raw}\n\n{summary_raw}\n\n{content_raw}"
            fb_caption = translate_for_facebook(full_text)
            if fb_caption != "Translation failed":
                fb_status = "Posted" if post_to_facebook(image_url, fb_caption) else "Failed"

        # === WordPress === (unchanged)
        wp_title, wp_content, wp_summary = "", "", ""
        wp_status = "Skipped"
        media_id, uploaded_image_url = None, None

        if source in ALLOWED_NEWS_DOMAINS:
            for _ in range(3):
                wp_title = translate_title(title_raw)
                wp_content = translate_for_wordpress(content_raw)
                wp_summary = translate_for_wordpress(summary_raw)
                if wp_title != "Translation failed" and wp_content != "Translation failed":
                    break
                time.sleep(2)

            media_id, uploaded_image_url = upload_image_to_wp(image_url)
            wp_status = "Posted" if post_to_wp(wp_title, wp_content, original_url, uploaded_image_url, media_id, news.get("sentiment")) else "Failed"


        all_results.append({
            "title": title_raw,
            "translated_facebook_post": fb_caption,
            "translated_title": wp_title,
            "translated_content": wp_content,
            "translated_summary": wp_summary,
            "original_url": original_url,
            "source": source,
            "image": image_url,
            "fb_status": fb_status,
            "wp_status": wp_status,
            "sentiment": news.get("sentiment", "unknown"),
            "timestamp": timestamp
        })

        time.sleep(1)

    # === Save JSON ===
    
    update_response_json(all_results)

    # === Summary Counts ===
    fb_success = sum(1 for item in all_results if item["fb_status"] == "Posted")
    wp_success = sum(1 for item in all_results if item["wp_status"] == "Posted")
    fb_failed = sum(1 for item in all_results if item["fb_status"] == "Failed")
    wp_failed = sum(1 for item in all_results if item["wp_status"] == "Failed")

    print(f"\n✅ Done! {len(all_results)} items processed.")
    print(f"📱 Facebook posts uploaded: {fb_success}")
    print(f"🌐 WordPress posts uploaded: {wp_success}")
    print(f"❌ Facebook failed: {fb_failed}")
    print(f"❌ WordPress failed: {wp_failed}")


if __name__ == "__main__":
    main()
