import os, requests, feedparser, json, re, subprocess

BOT_TOKEN = os.environ['BOT_TOKEN']
CHANNEL_ID = os.environ['CHANNEL_ID']

# ========== RSS ফিড লিস্ট ==========
RSS_FEEDS = [
    "https://www.scarleteen.com/rss.xml",
    "https://sexetc.org/feed/",
    "https://www.loveisrespect.org/feed/",
    "https://www.plannedparenthood.org/rss/news",
    "https://www.nhs.uk/rss/sexual-health.xml",
    "https://www.healthline.com/health-news/feed",
]

LOG_FILE = "posted_articles.json"

IMPORTANT_KEYWORDS = [
    "sex", "sexual", "consent", "condom", "sti", "std", "hiv",
    "pregnancy", "birth control", "contraceptive", "puberty",
    "menstruation", "period", "orgasm", "intimacy", "relationship",
    "dating", "love", "breakup", "safe sex", "protection",
    "lgbtq", "gay", "lesbian", "bisexual", "transgender",
    "harassment", "assault", "abuse", "rape", "trafficking",
    "health", "wellness", "mental health", "therapy",
    "body", "anatomy", "reproduction", "hormone",
    "teen", "adolescent", "young adult", "parent",
    "education", "guide", "tips", "advice"
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

def is_important(text):
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in IMPORTANT_KEYWORDS)

def build_message(feed_name, title, summary):
    """RSS থেকে সরাসরি বাংলা ফরম্যাটে পোস্ট"""
    return (
        f"🔹 <b>{title}</b>\n\n"
        f"📝 {summary[:350]}...\n\n"
        f"🌐 <i>Source: {feed_name}</i>\n"
        f"#SexEducation #IntimacySafety #AdultHealth #শিক্ষা"
    )

def fetch_first_important(posted_ids):
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
                combined = title + " " + summary
                if is_important(combined):
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

def git_commit_log():
    try:
        subprocess.run(["git", "config", "user.name", "GitHub Actions"], check=True)
        subprocess.run(["git", "config", "user.email", "actions@github.com"], check=True)
        subprocess.run(["git", "add", LOG_FILE], check=True)
        diff = subprocess.run(["git", "diff", "--cached", "--quiet"], capture_output=True)
        if diff.returncode != 0:
            subprocess.run(["git", "commit", "-m", "Update posted log"], check=True)
            subprocess.run(["git", "push"], check=True)
            print("✅ Log committed.")
        else:
            print("ℹ️  No change in log.")
    except Exception as e:
        print(f"⚠️  Git commit error: {e}")

def main():
    print("🔍 Scanning RSS feeds for important articles...")
    posted = load_posted()
    article_id, msg = fetch_first_important(posted)

    if msg:
        res = send_to_telegram(msg)
        if res.get('ok'):
            posted.add(article_id)
            save_posted(posted)
            print("✅ Post sent:", article_id[:60])
            git_commit_log()
        else:
            print("❌ Failed to post:", res)
    else:
        print("ℹ️  No important article found. Skipping.")

if __name__ == "__main__":
    main()
