import os, requests, feedparser, json, re, subprocess
from openai import OpenAI

BOT_TOKEN = os.environ['BOT_TOKEN']
CHANNEL_ID = os.environ['CHANNEL_ID']
DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY')

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

def generate_post(title, summary, source):
    prompt = f"""তুমি একজন যৌনশিক্ষা বিশেষজ্ঞ। নিচের টপিক নিয়ে বাংলায় একটি সম্পূর্ণ পোস্ট লিখো।

টপিক: {title}
সংক্ষিপ্ত তথ্য: {summary[:400]}
উৎস: {source}

নিয়ম:
- সম্পূর্ণ বাংলায় লিখবে
- গল্পের মতো সহজ ভাষায়
- "হ্যালো", "বাই", "গাইজ" এসব লিখবে না
- পোস্ট শেষ করবে, অর্ধেক রেখে থামবে না
- শেষে: সূত্র: {source}
- হ্যাশট্যাগ: #SexEducation #শিক্ষা"""

    response = deepseek.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=2000
    )
    return response.choices[0].message.content.strip()

def send_to_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    return requests.post(url, json={
        "chat_id": CHANNEL_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }).json()

def git_commit():
    subprocess.run(["git", "config", "user.name", "GitHub Actions"], check=True)
    subprocess.run(["git", "config", "user.email", "actions@github.com"], check=True)
    subprocess.run(["git", "add", LOG_FILE], check=True)
    result = subprocess.run(["git", "diff", "--cached", "--quiet"], capture_output=True)
    if result.returncode != 0:
        subprocess.run(["git", "commit", "-m", "Update log"], check=True)
        subprocess.run(["git", "push"], check=True)

def main():
    posted = load_posted()
    
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries:
                article_id = entry.get('id') or entry.get('link')
                if article_id in posted:
                    continue
                title = entry.title
                summary = clean_html(entry.summary if hasattr(entry, 'summary') else "")
                source = feed.feed.title if 'title' in feed.feed else feed_url
                
                post = generate_post(title, summary, source)
                res = send_to_telegram(post)
                
                if res.get('ok'):
                    posted.add(article_id)
                    save_posted(posted)
                    git_commit()
                    print("✅ Posted:", title[:50])
                    return
                else:
                    print("❌ Telegram error:", res)
        except Exception as e:
            print(f"⚠️ Error: {e}")
    
    print("ℹ️ No new topic found.")

if __name__ == "__main__":
    main()
