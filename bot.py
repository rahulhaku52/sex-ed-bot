import os, requests, feedparser, re

BOT_TOKEN = os.environ['BOT_TOKEN']
CHANNEL_ID = os.environ['CHANNEL_ID']

RSS_FEED = "https://www.who.int/feeds/entity/sexual-and-reproductive-health-and-research/en/rss.xml"

def clean_html(raw):
    return re.sub(r'<[^>]+>', '', raw).strip()

print("🔍 Fetching RSS...")
feed = feedparser.parse(RSS_FEED)
print(f"Number of entries: {len(feed.entries)}")

if not feed.entries:
    print("❌ RSS feed returned no entries. Possibly empty or blocked.")
else:
    entry = feed.entries[0]
    title = entry.title
    summary = entry.summary if hasattr(entry, 'summary') else ""
    summary_clean = clean_html(summary)[:300]
    msg = (
        f"📢 <b>Health Update | স্বাস্থ্য আপডেট</b>\n\n"
        f"🔹 <b>{title}</b>\n\n"
        f"📝 {summary_clean}...\n\n"
        f"<i>🔍 Source: World Health Organization (WHO)</i>\n"
        f"#WHO #HealthUpdate #SexEd #স্বাস্থ্যকথা"
    )
    print("Attempting to send to Telegram...")
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    res = requests.post(url, json={
        "chat_id": CHANNEL_ID,
        "text": msg,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }).json()
    print("API response:", res)
    if res.get('ok'):
        print("✅ SUCCESS: Post should be in your channel.")
    else:
        print("❌ FAILED: Check the response above for error.")
