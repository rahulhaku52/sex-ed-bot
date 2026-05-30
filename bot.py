import os, json, random, requests, subprocess

BOT_TOKEN = os.environ['BOT_TOKEN']
CHANNEL_ID = os.environ['CHANNEL_ID']
LOG_FILE = "posted_index.json"

# পোস্ট লোড
with open('posts.json', 'r', encoding='utf-8') as f:
    posts = json.load(f)

# আগের পোস্ট করা ইনডেক্স লোড
try:
    with open(LOG_FILE, 'r') as f:
        posted = set(json.load(f))
except:
    posted = set()

# বাকি পোস্টের ইনডেক্স
available = [i for i in range(len(posts)) if i not in posted]

if not available:
    # সব শেষ হলে আবার রিসেট
    posted = set()
    available = list(range(len(posts)))

# নতুন পোস্ট সিলেক্ট
idx = random.choice(available)
post = posts[idx]
posted.add(idx)

# লগ সেভ
with open(LOG_FILE, 'w') as f:
    json.dump(list(posted), f)

# টেলিগ্রামে পাঠান
url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
res = requests.post(url, json={
    "chat_id": CHANNEL_ID,
    "text": post['text'],
    "parse_mode": "HTML",
    "disable_web_page_preview": True
}).json()

print("✅ Posted" if res.get('ok') else f"❌ {res}")

# গিট কমিট
subprocess.run(["git", "config", "user.name", "GitHub Actions"], check=True)
subprocess.run(["git", "config", "user.email", "actions@github.com"], check=True)
subprocess.run(["git", "add", LOG_FILE], check=True)
result = subprocess.run(["git", "diff", "--cached", "--quiet"], capture_output=True)
if result.returncode != 0:
    subprocess.run(["git", "commit", "-m", "Update posted index"], check=True)
    subprocess.run(["git", "push"], check=True)
    print("✅ Log committed")
