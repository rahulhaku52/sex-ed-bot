import os, requests, feedparser, json, re, subprocess
from openai import OpenAI

BOT_TOKEN = os.environ['BOT_TOKEN']
CHANNEL_ID = os.environ['CHANNEL_ID']
DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY')

if not DEEPSEEK_API_KEY:
    raise Exception("DEEPSEEK_API_KEY not set!")

deepseek = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

RSS_FEEDS = [
    "https://www.scarleteen.com/rss.xml",
    "https://sexetc.org/feed/",
    "https://www.loveisrespect.org/feed/",
    "https://www.plannedparenthood.org/rss/news",
    "https://www.nhs.uk/rss/sexual-health.xml",
    "https://www.healthline.com/health-news/feed",
]

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

def clean_html(raw):
    return re.sub(r'<[^>]+>', '', raw).strip()

def generate_bangla_post(topic_title, topic_summary, source_name):
    """DeepSeek দিয়ে সম্পূর্ণ বাংলা পোস্ট তৈরি"""
    prompt = f"""তুমি একজন যৌনশিক্ষা বিশেষজ্ঞ। নিচের টপিক নিয়ে বাংলায় একটি সুন্দর, সহজ, এবং সম্পূর্ণ শিক্ষামূলক পোস্ট লিখো।

টপিক: {topic_title}
সংক্ষিপ্ত তথ্য: {topic_summary[:500]}
উৎস: {source_name}

গুরুত্বপূর্ণ নিয়ম:
- সম্পূর্ণ বাংলায় লিখবে, কোনো ইংরেজি শব্দ নয় (শুধু কনডম, STI, HIV-র মতো চিকিৎসা শব্দ ছাড়া)।
- লেখার ধরন হবে গল্পের মতো, বন্ধুর সাথে কথা বলার মতো, যেন পড়তে ভালো লাগে।
- শুরু করবে সরাসরি টপিক দিয়ে, কোনো "হ্যালো", "বাই", "গাইজ" নয়।
- পোস্ট সম্পূর্ণ করবে, শেষ বাক্যটি শেষ না করে থামবে না।
- শেষে দেবে: সূত্র: {source_name}
- হ্যাশট্যাগ: #SexEducation #IntimacySafety #AdultHealth #শিক্ষা
- ন্যূনতম ৩০০ শব্দ লিখবে।"""

    try:
        response = deepseek.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2500
        )
        text = response.choices[0].message.content.strip()
        # শেষে দাঁড়ি না থাকলে যোগ করে দিচ্ছি
        if not text.endswith(('.', '।', '?', '!')):
            text += '।'
        return text
    except Exception as e:
        print(f"❌ DeepSeek error: {e}")
        return None

def fetch_first_topic(posted_ids):
    """RSS থেকে প্রথম নতুন গুরুত্বপূর্ণ টপিক খুঁজে আনে"""
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
                # টপিক আছে? তাহলে নাও
                if title and summary:
                    clean_summary = clean_html(summary)
                    return article_id, title, clean_summary, feed_name
        except Exception as e:
            print(f"⚠️ Error parsing {feed_url}: {e}")
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
            print("✅ Log committed.")
        else:
            print("ℹ️  No change in log.")
    except Exception as e:
        print(f"⚠️  Git error: {e}")

def main():
    print("🔍 Fetching topic from RSS...")
    posted = load_posted()
    article_id, title, summary, source = fetch_first_topic(posted)

    if title:
        print(f"📝 Topic: {title}")
        post = generate_bangla_post(title, summary, source)
        if post:
            res = send_to_telegram(post)
            if res.get('ok'):
                posted.add(article_id)
                save_posted(posted)
                git_commit()
                print("✅ Bangla post sent!")
            else:
                print("❌ Telegram error:", res)
        else:
            print("❌ Failed to generate post.")
    else:
        print("ℹ️  No new topic found.")

if __name__ == "__main__":
    main()
