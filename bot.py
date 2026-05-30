import os, json, random, requests

BOT_TOKEN = os.environ['BOT_TOKEN']
CHANNEL_ID = os.environ['CHANNEL_ID']

with open('posts.json', 'r', encoding='utf-8') as f:
    posts = json.load(f)

post = random.choice(posts)

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
res = requests.post(url, json={
    "chat_id": CHANNEL_ID,
    "text": post['text'],
    "parse_mode": "HTML",
    "disable_web_page_preview": True
}).json()

print("✅ Posted" if res.get('ok') else f"❌ {res}")
