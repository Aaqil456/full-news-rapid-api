# Main function
def main():
    APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")
    EASY_PEASY_TRANSLATE_KEY = os.getenv("EASY_PEASY_TRANSLATE_KEY")

    if not APIFY_API_TOKEN:
        print("API token is missing! Please set APIFY_API_TOKEN as an environment variable.")
        return

    if not EASY_PEASY_TRANSLATE_KEY:
        print("Translation API key is missing! Please set EASY_PEASY_TRANSLATE_KEY as an environment variable.")
        return

    print("Fetching news from Apify Actor API...")
    fetched_news = fetch_news_from_apify(APIFY_API_TOKEN)

    print("Translating news content...")
    translated_news = []
    
    for news in fetched_news:
        original_title = news["title"]
        original_description = news["description"]
        original_content = news["content"]

        translated_title = translate_text_easypeasy(EASY_PEASY_TRANSLATE_KEY, original_title)
        translated_description = translate_text_easypeasy(EASY_PEASY_TRANSLATE_KEY, original_description)
        translated_content = translate_text_easypeasy(EASY_PEASY_TRANSLATE_KEY, original_content)

        # Check if any translation succeeded
        if translated_title != "Translation failed" or translated_description != "Translation failed" or translated_content != "Translation failed":
            news["title"] = translated_title if translated_title != "Translation failed" else original_title
            news["description"] = translated_description if translated_description != "Translation failed" else original_description
            news["content"] = translated_content if translated_content != "Translation failed" else original_content
            translated_news.append(news)
        else:
            print(f"Skipping news (translation failed for all fields): {original_title}")

    existing_data = load_existing_data()
    combined_news = remove_duplicates(translated_news + existing_data.get("all_news", []))

    save_to_json(combined_news)

    print("\nNewly Added News:")
    new_news = [news for news in combined_news if news not in existing_data.get("all_news", [])]
    for news in new_news:
        print(f"Title: {news['title']}\nURL: {news['url']}\nContent Snippet: {news.get('content', '')[:100]}...\n")

if __name__ == "__main__":
    main()
