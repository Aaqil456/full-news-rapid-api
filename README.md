Sure! Here's a **complete README.md** documentation for your project, designed to be clear, professional, and GitHub-ready:  

---

# 🚀 Crypto News Translator & WordPress Publisher

This project automates the process of fetching crypto news from **Cointelegraph.com News**, translating it into **Malay** using **Google Gemini AI**, and publishing it directly to **WordPress**, complete with featured images and proper formatting.

---

## 🔑 Features

✅ Automatically fetches the latest crypto news using **APIFY Actor**.  
✅ Translates titles and content to **Malay** with **Google Gemini API** while removing advertisement-like sentences.  
✅ Downloads article images, uploads them to the **WordPress Media Library**, and sets them as the **featured image**.  
✅ Posts the translated articles directly to WordPress under the **News** category with proper structure.  
✅ Includes the original source link at the end of each article.  
✅ Filters only news from **Cointelegraph.com News**.  
✅ Runs fully automated via **GitHub Actions**.

---

## 🏗️ Project Architecture

```
[APIFY] → Fetch Crypto News
        ↓
[Google Gemini AI] → Translate Title, Description, Content
        ↓
[Python] → Upload Images → WordPress Media Library
        ↓
[WordPress REST API] → Publish Post
        ↓
[GitHub Actions] → Scheduled Automation
```

---

## 🔧 Tech Stack

- **Python 3.8+**
- **Google Gemini AI API**
- **APIFY API**
- **WordPress REST API**
- **GitHub Actions**
- **JSON handling**
- **Requests library**

---

## ⚙️ Setup Instructions

### 1️⃣ Clone the repository:
```bash
git clone https://github.com/yourusername/crypto-news-translator.git
cd crypto-news-translator
```

### 2️⃣ Install dependencies:
```bash
pip install -r requirements.txt
```

### 3️⃣ Configure Environment Variables:

Create a `.env` file or set the following environment variables:
```
GEMINI_API_KEY=your_gemini_api_key
APIFY_API_TOKEN=your_apify_api_token
WP_URL=https://yourwebsite.com/wp-json/wp/v2
WP_USER=your_wordpress_username
WP_APP_PASSWORD=your_wordpress_application_password
```

### 4️⃣ Run the script locally:
```bash
python cryptonews_translator.py
```

---

## ⚡ GitHub Actions Automation

This project includes a GitHub Actions workflow (`.github/workflows/translation.yml`) that:
- Runs on a schedule (or manually).
- Executes the entire pipeline automatically.
- Commits updated JSON logs.
- Optionally triggers a WordPress rebuild.

---

## 📁 Output Example

Every successful run updates `translated_news.json`:
```json
{
  "timestamp": "2025-03-06 07:27:05",
  "all_news": [
    {
      "title": "Bitcoin Sasar Tarikh ‘Pelancaran’...",
      "description": "...",
      "content": "...",
      "image": "https://yourwebsite.com/wp-content/uploads/2025/03/image.jpg",
      "url": "https://original-article.com",
      "source": "Cointelegraph.com News",
      "timestamp": "2025-03-06T07:04:00Z",
      "status": "Posted"
    }
  ]
}
```

---

## 📌 Notes

- Only processes articles from **Cointelegraph.com News**.
- If the image cannot be downloaded (403 error), the post is still published without an image.
- The script adds a proper **User-Agent header** to bypass basic hotlink protections when downloading images.
- Advertisement-like sentences are filtered during translation.

---

## 🤝 Contributing

Feel free to fork, submit issues, or create pull requests if you'd like to enhance this project!

---

## 📬 Contact

For questions, collaborations, or custom automation:
- LinkedIn: [Your LinkedIn Profile](https://linkedin.com/in/yourprofile)
- Twitter (X): [@yourhandle](https://twitter.com/yourhandle)

---

## ⭐ License

MIT License. Free to use and modify.

---

Would you like me to:
✅ Add this directly into your GitHub repo?  
✅ Provide a matching **`requirements.txt`** for easy installation?
