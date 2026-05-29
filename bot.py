import os, requests, feedparser, json, random, re, subprocess

BOT_TOKEN = os.environ['BOT_TOKEN']
CHANNEL_ID = os.environ['CHANNEL_ID']

RSS_FEED = "https://www.who.int/feeds/entity/sexual-and-reproductive-health-and-research/en/rss.xml"
LOG_FILE = "posted_articles.json"

def load_posted():
    try:
        with open(LOG_FILE, 'r') as f:
            return set(json.load(f))
    except:
        return set()

def save_posted(posted):
    with open(LOG_FILE, 'w') as f:
        json.dump(list(posted), f)

def clean_html(raw_html):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext.strip()

def create_mixed_message(title, summary_en):
    """ইংলিশ টাইটেল ও সামারিকে বাংলা-ইংলিশ মিক্সে রিরাইট করবে"""
    message = (
        f"📢 <b>Health Update | স্বাস্থ্য আপডেট</b>\n\n"
        f"🔹 <b>{title}</b>\n\n"
        f"📝 {summary_en[:250]}...\n\n"
        f"<i>🔍 Source: World Health Organization (WHO)</i>\n"
        f"#WHO #HealthUpdate #SexEd #স্বাস্থ্যকথা"
    )
    return message

def fetch_new_article(posted_guids):
    feed = feedparser.parse(RSS_FEED)
    for entry in feed.entries:
        article_id = entry.get('id') or entry.get('link')
        if article_id not in posted_guids:
            title = entry.title
            summary = entry.summary if hasattr(entry, 'summary') else ""
            summary_clean = clean_html(summary)
            msg = create_mixed_message(title, summary_clean)
            return article_id, msg
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

def git_commit():
    """পরিবর্তিত posted_articles.json গিটে কমিট করে দেবে"""
    try:
        subprocess.run(["git", "config", "user.name", "GitHub Action"], check=True)
        subprocess.run(["git", "config", "user.email", "action@github.com"], check=True)
        subprocess.run(["git", "add", LOG_FILE], check=True)
        # কমিট করার মতো কিছু থাকলেই কেবল কমিট
        diff = subprocess.run(["git", "diff", "--cached", "--quiet"], capture_output=True)
        if diff.returncode != 0:  # পরিবর্তন আছে
            subprocess.run(["git", "commit", "-m", "Update posted articles log"], check=True)
            subprocess.run(["git", "push"], check=True)
            print("✅ Log committed to repository.")
        else:
            print("ℹ️ No change in log, skipping commit.")
    except Exception as e:
        print(f"⚠️ Git commit failed: {e}")

def main():
    posted = load_posted()
    article_id, message = fetch_new_article(posted)
    if message:
        res = send_to_telegram(message)
        if res.get('ok'):
            posted.add(article_id)
            save_posted(posted)
            print("✅ New WHO update posted:", article_id)
            git_commit()  # লগ সেভ করতে গিটে পুশ
        else:
            print("❌ Failed to post:", res)
    else:
        print("ℹ️ No new article in WHO feed. Trying own bank...")
        try:
            with open('posts.json', 'r', encoding='utf-8') as f:
                posts = json.load(f)
            if posts:
                text = random.choice(posts)['text']
                send_to_telegram(text)
                print("📋 Posted from own bank.")
            else:
                print("⚠️ Bank empty.")
        except:
            print("❌ No posts.json found.")

if __name__ == "__main__":
    main()
