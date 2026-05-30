import os, requests, feedparser, json, re, subprocess
import google.generativeai as genai

BOT_TOKEN = os.environ['BOT_TOKEN']
CHANNEL_ID = os.environ['CHANNEL_ID']
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.0-flash')

RSS_FEEDS = [
    "https://www.scarleteen.com/rss.xml",
    "https://sexetc.org/feed/",
    "https://www.loveisrespect.org/feed/",
]

LOG_FILE = "posted_articles.json"

IMPORTANT_KEYWORDS = [
    "sex", "sexual", "consent", "How to sex", "what is the appy position in sex", "oral", "how to oral", "condom", "sti", "std", "hiv",
    "pregnancy", "birth control", "contraceptive", "puberty",
    "menstruation", "period", "orgasm", "intimacy", "relationship",
    "dating", "love", "breakup", "safe sex", "protection",
    "lgbtq", "gay", "lesbian", "bisexual", "transgender",
    "health", "wellness", "mental health", "body", "anatomy"
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

def generate_bangla_story(title, summary_en, source_name):
    """Gemini দিয়ে সম্পূর্ণ বাংলা গল্প জেনারেট"""
    prompt = f"""You are a Bengali sex educator. Write a LONG, story-style educational post COMPLETELY in Bengali language. Not a single English word except medical terms like condom, STI.

Topic: {title}
Reference: {summary_en[:400]}
Source: {source_name}

Requirements:
- Start with the title in Bengali
- Write in warm, conversational Bengali storytelling style (like a friend explaining)
- Minimum 400-500 words, maximum 700 words
- Include:
  * Realistic scenario or example
  * Scientific facts explained simply
  * Practical tips or advice
  * Emotional aspects
- End with:
  * A motivational or thoughtful closing line
  * Source credit: সূত্র: {source_name}
  * Hashtags: #SexEducation #IntimacySafety #AdultHealth #শিক্ষা
- NO markdown, NO links, NO English sentences
- Pure Bengali characters"""
    
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"⚠️ Gemini error: {e}")
        return None

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
                    bangla_story = generate_bangla_story(title, clean_summary, feed_name)
                    if bangla_story:
                        return article_id, bangla_story
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
    print("🔍 Scanning RSS feeds for Bangla story generation...")
    posted = load_posted()
    article_id, msg = fetch_first_important(posted)

    if msg:
        res = send_to_telegram(msg)
        if res.get('ok'):
            posted.add(article_id)
            save_posted(posted)
            print("✅ Bangla story posted!")
            git_commit_log()
        else:
            print("❌ Failed:", res)
    else:
        print("ℹ️  No suitable article found or Gemini quota exceeded.")

if __name__ == "__main__":
    main()
