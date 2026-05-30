import os, requests, feedparser, json, re, subprocess
from openai import OpenAI

BOT_TOKEN = os.environ['BOT_TOKEN']
CHANNEL_ID = os.environ['CHANNEL_ID']
DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY')

if not DEEPSEEK_API_KEY:
    raise Exception("DEEPSEEK_API_KEY not set!")

deepseek_client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

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
    """DeepSeek দিয়ে নিখুঁত বাংলা গল্প"""
    prompt = f"""You are a native Bengali sex educator. Write a COMPLETE, long educational story-style post in PURE BENGALI language. 

Topic: {title}
Reference info: {summary_en[:400]}
Source: {source_name}

STRICT RULES:
- Write 100% in Bengali. No English words except unavoidable medical terms (condom, STI, HIV).
- DO NOT use "হ্যালো", "বাই", "গাইজ", or any direct translation from English.
- Start naturally with the topic, like a friend telling a story. For example: "কনডম ব্যবহার নিয়ে আমাদের সমাজে অনেক ভুল ধারণা আছে। আজ আমি তোমাকে একটা গল্প বলি..."
- Length: minimum 400 words, complete the story properly with a conclusion.
- Include: a relatable scenario, scientific facts, practical tips, emotional aspects.
- End with: "সূত্র: {source_name}" and hashtags: #SexEducation #IntimacySafety #AdultHealth #শিক্ষা
- Do NOT cut off mid-sentence. Finish the entire thought.
"""
    try:
        response = deepseek_client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2500  # লম্বা আউটপুটের জন্য বাড়ানো হয়েছে
        )
        text = response.choices[0].message.content.strip()
        # যদি কোনো কারণে কাটা পড়ে, তবে শেষ বাক্যটি সম্পূর্ণ আছে কিনা চেক (বেসিক)
        if not text.endswith(('.', '।', '?', '!', ')')):
            text += '।'  # শেষে দাঁড়ি যোগ
        return text
    except Exception as e:
        print(f"❌ DeepSeek error: {e}")
        return None

def build_rss_fallback(feed_name, title, summary):
    """DeepSeek ব্যর্থ হলে RSS সরাসরি"""
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
                    # প্রথমে বাংলা গল্প জেনারেট
                    story = generate_bangla_story(title, clean_summary, feed_name)
                    if story:
                        return article_id, story
                    # ব্যর্থ হলে RSS ফরম্যাট
                    return article_id, build_rss_fallback(feed_name, title, clean_summary)
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
