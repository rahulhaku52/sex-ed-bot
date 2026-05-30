import os, requests, feedparser, json, re, subprocess

BOT_TOKEN = os.environ['BOT_TOKEN']
CHANNEL_ID = os.environ['CHANNEL_ID']

# ========== API Keys ==========
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')

# ========== API Clients ==========
# Gemini
gemini_model = None
if GEMINI_API_KEY:
    import google.generativeai as genai
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-2.0-flash')

# DeepSeek
deepseek_client = None
if DEEPSEEK_API_KEY:
    from openai import OpenAI
    deepseek_client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

# Groq
groq_client = None
if GROQ_API_KEY:
    from groq import Groq
    groq_client = Groq(api_key=GROQ_API_KEY)

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
    "how to sex", "sexual", "advice", "young adult", 
    "education", "guide", "tips", "advice"
]

BANGLA_PROMPT = """Write a LONG educational post in Bengali language (Bangla). 
Topic: {title}
Reference: {summary}
Source: {source}

Requirements:
- Write completely in Bengali (not English)
- Story-style, engaging, warm conversational tone
- 400-500 words
- Include practical tips and scientific facts
- End with source credit: সূত্র: {source}
- Hashtags: #SexEducation #IntimacySafety #AdultHealth #শিক্ষা"""

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

def try_deepseek(prompt):
    if not deepseek_client:
        return None
    try:
        response = deepseek_client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
            max_tokens=1500
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"  ❌ DeepSeek error: {e}")
        return None

def try_gemini(prompt):
    if not gemini_model:
        return None
    try:
        response = gemini_model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"  ❌ Gemini error: {e}")
        return None

def try_groq(prompt):
    if not groq_client:
        return None
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
            max_tokens=1500
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"  ❌ Groq error: {e}")
        return None

def generate_bangla_story(title, summary_en, source_name):
    prompt = BANGLA_PROMPT.format(title=title, summary=summary_en[:400], source=source_name)
    
    # ১. DeepSeek (সবচেয়ে নির্ভরযোগ্য ফ্রি)
    print("  🟡 Trying DeepSeek...")
    result = try_deepseek(prompt)
    if result:
        print("  ✅ DeepSeek success!")
        return result
    
    # ২. Gemini
    print("  🟡 Trying Gemini...")
    result = try_gemini(prompt)
    if result:
        print("  ✅ Gemini success!")
        return result
    
    # ৩. Groq
    print("  🟡 Trying Groq...")
    result = try_groq(prompt)
    if result:
        print("  ✅ Groq success!")
        return result
    
    print("  ❌ All APIs failed!")
    return None

def build_rss_fallback(feed_name, title, summary):
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
                    bangla_story = generate_bangla_story(title, clean_summary, feed_name)
                    if bangla_story:
                        return article_id, bangla_story
                    msg = build_rss_fallback(feed_name, title, clean_summary)
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
    print("🔍 Scanning RSS feeds...")
    posted = load_posted()
    article_id, msg = fetch_first_important(posted)

    if msg:
        res = send_to_telegram(msg)
        if res.get('ok'):
            posted.add(article_id)
            save_posted(posted)
            print("✅ Post sent!")
            git_commit_log()
        else:
            print("❌ Failed:", res)
    else:
        print("ℹ️  No important article found.")

if __name__ == "__main__":
    main()
