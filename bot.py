import os, requests, feedparser, json, re, subprocess

BOT_TOKEN = os.environ['BOT_TOKEN']
CHANNEL_ID = os.environ['CHANNEL_ID']

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
    
    "কনডম ব্যবহারের সঠিক নিয়ম ও ভুল ধারণা",
    "সম্মতি (Consent) কী ও কেন জরুরি",
    "পিরিয়ড বা মাসিক চক্র সম্পর্কে সঠিক তথ্য",
    "যৌন সংক্রমণ (STI) প্রতিরোধের উপায়",
    "বয়ঃসন্ধিকালে শরীরের পরিবর্তন",
    "নিরাপদ যৌনতা (Safe Sex) কী",
    "সম্পর্কের মূল ভিত্তি: বিশ্বাস ও শ্রদ্ধা",
    "মাস্টারবেশন নিয়ে ভুল ধারণা ও সত্য",
    "জন্মনিয়ন্ত্রণ পদ্ধতি সম্পর্কে জানা",
    "LGBTQIA+ কমিউনিটি বোঝা",
    "মানসিক স্বাস্থ্য ও যৌনতা",
    "প্রথম যৌন সম্পর্কের আগে যে বিষয়গুলো জানা জরুরি",
    "যৌন নিপীড়ন (Sexual Harassment) কী ও প্রতিকার",
    "নারীর যৌন স্বাস্থ্য",
    "পুরুষের যৌন স্বাস্থ্য",
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

def build_post(title, summary, source):
    return (
        f"🔹 <b>{title}</b>\n\n"
        f"📝 {summary[:350]}...\n\n"
        f"🌐 <i>Source: {source}</i>\n"
        f"#SexEducation #IntimacySafety #AdultHealth #শিক্ষা"
    )

def fetch_first_topic(posted_ids):
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            source = feed.feed.title if 'title' in feed.feed else feed_url
            for entry in feed.entries:
                article_id = entry.get('id') or entry.get('link')
                if article_id in posted_ids:
                    continue
                title = entry.title
                summary = entry.summary if hasattr(entry, 'summary') else ""
                combined = title + " " + summary
                if is_important(combined):
                    clean_summary = clean_html(summary)
                    return article_id, title, clean_summary, source
        except Exception as e:
            print(f"⚠️ Error: {e}")
    return None, None, None, None

def send_to_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    return requests.post(url, json={
        "chat_id": CHANNEL_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }).json()

def git_commit():
    try:
        subprocess.run(["git", "config", "user.name", "GitHub Actions"], check=True)
        subprocess.run(["git", "config", "user.email", "actions@github.com"], check=True)
        subprocess.run(["git", "add", LOG_FILE], check=True)
        diff = subprocess.run(["git", "diff", "--cached", "--quiet"], capture_output=True)
        if diff.returncode != 0:
            subprocess.run(["git", "commit", "-m", "Update log"], check=True)
            subprocess.run(["git", "push"], check=True)
            print("✅ Log saved")
    except Exception as e:
        print(f"⚠️ Git error: {e}")

def main():
    print("🔍 Scanning RSS feeds...")
    posted = load_posted()
    article_id, title, summary, source = fetch_first_topic(posted)

    if title:
        post = build_post(title, summary, source)
        res = send_to_telegram(post)
        if res.get('ok'):
            posted.add(article_id)
            save_posted(posted)
            git_commit()
            print("✅ Posted:", title[:50])
        else:
            print("❌ Telegram error:", res)
    else:
        print("ℹ️ No new topic found.")

if __name__ == "__main__":
    main()
