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

def generate_bangla_story(title, summary_en, source_name):
    """Gemini দিয়ে বাংলায় গল্পের মতো শিক্ষামূলক পোস্ট তৈরি"""
    prompt = f"""
You are a professional sex educator writing for a Bengali audience. Write an educational, story-style post in BENGALI language (not English). Use simple, engaging Bengali that feels like a friendly conversation or a short informative story. Include these key elements from the original article:

Article Title: {title}
Summary: {summary_en[:500]}
Source: {source_name}

Make the post:
- Start with the article title as the headline
- Write in fluent Bengali (not Banglish)
- Keep it 400-3000 words
- Include practical tips if relevant
- End with hashtags: #SexEducation #IntimacySafety #AdultHealth #শিক্ষা
- Mention "Source: {source_name}" at the end
- Do NOT include any links
"""
    try:
        response = model.generate_content(prompt)
        ai_text = response.text.strip()
        return ai_text
    except Exception as e:
        print(f"⚠️ Gemini error: {e}")
        return None

def fetch_first_important(posted_ids):
    """RSS থেকে প্রথম গুরুত্বপূর্ণ আর্টিকেল খুঁজে Gemini দিয়ে বাংলা পোস্ট বানাও"""
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
                    # Gemini দিয়ে বাংলা পোস্ট তৈরি করো
                    bangla_post = generate_bangla_story(title, clean_summary, feed_name)
                    if bangla_post:
                        return article_id, bangla_post
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
            print("✅ Bangla post sent:", article_id[:60])
            git_commit_log()
        else:
            print("❌ Failed to post:", res)
    else:
        print("ℹ️  No important article found. Skipping.")

if __name__ == "__main__":
    main()
