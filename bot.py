import os, requests, feedparser, json, random, time

BOT_TOKEN = os.environ['BOT_TOKEN']
CHANNEL_ID = os.environ['CHANNEL_ID']

# RSS ফিড (WHO Reproductive Health)
RSS_FEED = "https://www.who.int/feeds/entity/sexual-and-reproductive-health-and-research/en/rss.xml"
LOG_FILE = "posted_articles.json"  # আগে পোস্ট হয়েছে এমন আর্টিকেলের তালিকা

def load_posted_articles():
    try:
        with open(LOG_FILE, 'r') as f:
            return set(json.load(f))
    except:
        return set()

def save_posted_articles(posted):
    with open(LOG_FILE, 'w') as f:
        json.dump(list(posted), f)

def fetch_new_article(posted_guids):
    feed = feedparser.parse(RSS_FEED)
    for entry in feed.entries:
        if entry.get('id') not in posted_guids:
            title = entry.title
            link = entry.link
            summary = entry.summary if hasattr(entry, 'summary') else ""
            # ক্লিনিং: HTML ট্যাগ বাদ
            import re
            summary_clean = re.sub('<[^<]+?>', '', summary)
            summary_clean = summary_clean.strip()[:300]
            # রিরাইট: নিজস্ব টেমপ্লেট
            message = (
                f"📚 <b>স্বাস্থ্য আপডেট</b>\n\n"
                f"👉 {title}\n\n"
                f"💡 {summary_clean}...\n\n"
                f"🔍 <i>Source: World Health Organization (WHO)</i>\n"
                f"#WHO #SexEd #স্বাস্থ্যকথা"
            )
            return entry.get('id'), message
    return None, None

def send_to_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHANNEL_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    return requests.post(url, json=payload).json()

def main():
    posted = load_posted_articles()
    article_id, message = fetch_new_article(posted)
    if message:
        res = send_to_telegram(message)
        if res.get('ok'):
            posted.add(article_id)
            save_posted_articles(posted)
            print("Posted new WHO update:", article_id)
        else:
            print("Failed to post:", res)
    else:
        # ফলস্বরূপ: ফিডে নতুন কিছু না থাকলে পোস্ট ব্যাংক থেকে একটি র‌্যান্ডম পোস্ট নেবে
        try:
            with open('posts.json', 'r', encoding='utf-8') as f:
                posts = json.load(f)
            if posts:
                text = random.choice(posts)['text']
                send_to_telegram(text)
                print("Posted from own bank.")
            else:
                print("No posts in bank.")
        except:
            print("No posts.json found or empty.")

if __name__ == "__main__":
    main()
