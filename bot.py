import os, requests, feedparser, json, random, re, subprocess

BOT_TOKEN = os.environ['BOT_TOKEN']
CHANNEL_ID = os.environ['CHANNEL_ID']

# RSS feed (WHO Sexual and Reproductive Health)
RSS_FEED = "https://www.who.int/feeds/entity/sexual-and-reproductive-health-and-research/en/rss.xml"
LOG_FILE = "posted_articles.json"

def load_posted():
    """ আগে পোস্ট করা আর্টিকেলের আইডি লোড করো """
    try:
        with open(LOG_FILE, 'r') as f:
            return set(json.load(f))
    except:
        return set()

def save_posted(posted):
    """ পোস্ট করা আইডি সেট ফাইলে সংরক্ষণ করো """
    with open(LOG_FILE, 'w') as f:
        json.dump(list(posted), f)

def clean_html(raw):
    """ HTML ট্যাগ সরিয়ে পরিষ্কার টেক্সট দাও """
    return re.sub(r'<[^>]+>', '', raw).strip()

def build_rss_message(title, summary):
    """ RSS থেকে পাওয়া তথ্য দিয়ে সুন্দর মেসেজ তৈরি """
    return (
        f"📢 <b>Health Update | স্বাস্থ্য আপডেট</b>\n\n"
        f"🔹 <b>{title}</b>\n\n"
        f"📝 {summary[:300]}...\n\n"
        f"<i>🔍 Source: World Health Organization (WHO)</i>\n"
        f"#WHO #HealthUpdate #SexEd #স্বাস্থ্যকথা"
    )

def fetch_new_article(posted_ids):
    """ RSS থেকে একটি নতুন আর্টিকেল খুঁজে বের করো """
    feed = feedparser.parse(RSS_FEED)
    for entry in feed.entries:
        article_id = entry.get('id') or entry.get('link')
        if article_id not in posted_ids:
            title = entry.title
            summary = entry.summary if hasattr(entry, 'summary') else ""
            clean_summary = clean_html(summary)
            msg = build_rss_message(title, clean_summary)
            return article_id, msg
    return None, None

def send_to_telegram(text):
    """ টেলিগ্রাম API ব্যবহার করে মেসেজ পাঠাও """
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHANNEL_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    resp = requests.post(url, json=payload)
    return resp.json()

def git_commit_log():
    """ posted_articles.json ফাইল গিটে কমিট ও পুশ করো """
    try:
        subprocess.run(["git", "config", "user.name", "GitHub Actions"], check=True)
        subprocess.run(["git", "config", "user.email", "actions@github.com"], check=True)
        subprocess.run(["git", "add", LOG_FILE], check=True)
        diff = subprocess.run(["git", "diff", "--cached", "--quiet"], capture_output=True)
        if diff.returncode != 0:
            subprocess.run(["git", "commit", "-m", "Update posted log"], check=True)
            subprocess.run(["git", "push"], check=True)
            print("✅ Log committed to repo.")
        else:
            print("ℹ️  No change in log, skipping commit.")
    except Exception as e:
        print(f"⚠️  Git commit error (non-fatal): {e}")

def fallback_bank_post():
    """ যদি RSS নতুন না দেয়, তাহলে posts.json থেকে র‌্যান্ডম পোস্ট নাও """
    try:
        with open('posts.json', 'r', encoding='utf-8') as f:
            posts = json.load(f)
        if posts:
            post = random.choice(posts)
            return post['text']
    except Exception as e:
        print(f"⚠️  posts.json পড়তে সমস্যা: {e}")
    return None

def main():
    print("🔍 Checking RSS feed...")
    posted = load_posted()
    article_id, message = fetch_new_article(posted)

    if message:
        print("✅ New article found. Sending to Telegram...")
        res = send_to_telegram(message)
        if res.get('ok'):
            posted.add(article_id)
            save_posted(posted)
            print("🎉 WHO article posted successfully:", article_id)
            git_commit_log()
        else:
            print("❌ Failed to send RSS post. API response:", res)
    else:
        print("ℹ️  No new article in RSS. Trying posts.json bank...")
        bank_msg = fallback_bank_post()
        if bank_msg:
            print("📋 Sending from own bank...")
            res = send_to_telegram(bank_msg)
            if res.get('ok'):
                print("✅ Own bank post sent.")
            else:
                print("❌ Bank post failed. API response:", res)
        else:
            print("❌ No posts.json found or empty. Nothing to post.")

if __name__ == "__main__":
    main()
