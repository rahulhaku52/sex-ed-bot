import os, json, random, requests, sys

print("🔵 Script started")
print("🔵 Current working directory:", os.getcwd())
print("🔵 Files in directory:", os.listdir('.'))

BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHANNEL_ID = os.environ.get('CHANNEL_ID')

if not BOT_TOKEN or not CHANNEL_ID:
    print("❌ ERROR: BOT_TOKEN or CHANNEL_ID not set.")
    sys.exit(1)

print(f"🔵 BOT_TOKEN starts with: {BOT_TOKEN[:10]}...")
print(f"🔵 CHANNEL_ID: {CHANNEL_ID}")

def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHANNEL_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    print("🔵 Sending POST request to Telegram...")
    try:
        resp = requests.post(url, json=payload, timeout=10)
        print(f"🔵 HTTP Status: {resp.status_code}")
        data = resp.json()
        print(f"🔵 Response JSON: {data}")
        return data
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return None

def main():
    print("🔵 Attempting to load posts.json...")
    try:
        with open('posts.json', 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"🔵 posts.json raw content (first 200 chars): {content[:200]}")
            posts = json.loads(content)
        print(f"🔵 Loaded {len(posts)} posts.")
        if not posts:
            print("❌ posts.json is empty. Exiting.")
            return
    except FileNotFoundError:
        print("❌ posts.json file NOT FOUND. Make sure it's in the repository root and committed.")
        return
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in posts.json: {e}")
        return
    except Exception as e:
        print(f"❌ Error reading posts.json: {e}")
        return

    post = random.choice(posts)
    text = post.get('text')
    if not text:
        print("❌ Selected post has no 'text' field.")
        return
    print(f"🔵 Selected post (first 100 chars): {text[:100]}")
    result = send_message(text)
    if result and result.get('ok'):
        print("✅ SUCCESS: Message sent to channel!")
    else:
        print("❌ FAILED: Message not sent. Check response above.")

if __name__ == "__main__":
    main()
