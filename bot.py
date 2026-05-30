import os, requests, feedparser, json, re, subprocess

BOT_TOKEN = os.environ['BOT_TOKEN']
CHANNEL_ID = os.environ['CHANNEL_ID']
LOG_FILE = "posted_articles.json"

RSS_FEEDS = [
    "https://www.scarleteen.com/rss.xml",
    "https://sexetc.org/feed/",
    "https://www.loveisrespect.org/feed/",
    "https://www.plannedparenthood.org/rss/news",
    "https://www.nhs.uk/rss/sexual-health.xml",
    "https://www.healthline.com/health-news/feed",
]

def load_posted():
    try:
        with open(LOG_FILE, 'r') as f:
            return set(json.load(f))
    except:
        return set()

def save_posted(posted):
    with open(LOG_FILE, 'w') as f:
        json.dump(list(posted), f)

def clean_html(raw):
    return re.sub(r'<[^>]+>', '', raw).strip()

def build_message(feed_title, title, summary):
    return (
        f"📚 <b>যৌনশিক্ষা ও সম্পর্ক টিপস</b>\n\n"
        f"🔹 <b>{title}</b>\n\n"
        f"📝 {summary[:300]}...\n\n"
        f"🌐 <i>Source: {feed_title}</i>\n"
        f"#SexEducation #IntimacySafety #AdultHealth #শিক্ষা"
    )

def fetch_first_new(posted_ids):
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            feed_name = feed.feed.title if 'title' in feed.feed else feed_url
            for entry in feed.entries:
                article_id = entry.get('id') or entry.get('link')
                if article_id in posted_ids:
                    continue
                title = entry.title
                summary = entry.summary if hasattr(entry, 'summary') else ""
                clean_summary = clean_html(summary)
                msg = build_message(feed_name, title, clean_summary)
                return article_id, msg
        except Exception as e:
            print(f"⚠️ Error parsing {feed_url}: {e}")
    return None, None

def send_to_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    return requests.post(url, json={
        "chat_id": CHANNEL_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }).json()

def git_commit():
    """গিট কমিট ও পুশ (এবার নিশ্চিত)"""
    try:
        subprocess.run(["git", "config", "user.name", "GitHub Actions"], check=True)
        subprocess.run(["git", "config", "user.email", "actions@github.com"], check=True)
        subprocess.run(["git", "add", LOG_FILE], check=True)
        # কোনো পরিবর্তন থাকলেই কমিট করবো
        result = subprocess.run(["git", "diff", "--cached", "--quiet"], capture_output=True)
        if result.returncode != 0:
            subprocess.run(["git", "commit", "-m", "Update posted log"], check=True)
            subprocess.run(["git", "push"], check=True)
            print("✅ Log committed & pushed.")
        else:
            print("ℹ️ No change in log.")
    except Exception as e:
        print(f"❌ Git commit error: {e}")

def main():
    print("🔍 Checking RSS feeds...")
    posted = load_posted()
    article_id, msg = fetch_first_new(posted)
    if msg:
        res = send_to_telegram(msg)
        if res.get('ok'):
            posted.add(article_id)
            save_posted(posted)
            print("✅ Posted:", article_id[:60])
            git_commit()  # পুশ করতেই হবে
        else:
            print("❌ Failed:", res)
    else:
        print("ℹ️ No new articles.")

if __name__ == "__main__":
    main()
