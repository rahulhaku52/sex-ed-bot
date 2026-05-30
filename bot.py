import os, requests, feedparser, json, re

BOT_TOKEN = os.environ['BOT_TOKEN']
CHANNEL_ID = os.environ['CHANNEL_ID']
CACHE_FILE = "posted_cache.json"  # ক্যাশ ফাইলের নাম

RSS_FEEDS = [
    "https://www.scarleteen.com/rss.xml",
    "https://sexetc.org/feed/",
    "https://www.loveisrespect.org/feed/",
    "https://www.plannedparenthood.org/rss/news",
    "https://www.nhs.uk/rss/sexual-health.xml",
    "https://www.healthline.com/health-news/feed",
]

def load_posted():
    """ক্যাশ থেকে পোস্ট করা আইডি সেট লোড করো"""
    try:
        with open(CACHE_FILE, 'r') as f:
            return set(json.load(f))
    except:
        return set()

def save_posted(posted):
    """ক্যাশে আইডি সেট সংরক্ষণ করো (Actions post-job ক্যাশ স্টেপের জন্য)"""
    with open(CACHE_FILE, 'w') as f:
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
    """সব ফিড থেকে প্রথম নতুন (আগে পোস্ট হয়নি এমন) আর্টিকেল বের করো"""
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

def main():
    print("🔍 Checking RSS feeds...")
    posted = load_posted()
    article_id, msg = fetch_first_new(posted)
    if msg:
        res = send_to_telegram(msg)
        if res.get('ok'):
            posted.add(article_id)
            save_posted(posted)  # ক্যাশ ফাইল আপডেট
            print("✅ New article posted:", article_id[:60])
        else:
            print("❌ Failed to post:", res)
    else:
        print("ℹ️ No new articles. Skipping.")

if __name__ == "__main__":
    main()
