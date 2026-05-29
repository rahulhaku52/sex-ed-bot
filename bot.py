import os, json, random, requests

BOT_TOKEN = os.environ['BOT_TOKEN']
CHANNEL_ID = os.environ['CHANNEL_ID']

def get_random_post():
    with open('posts.json', 'r', encoding='utf-8') as f:
        posts = json.load(f)
    if not posts:
        return None
    return random.choice(posts)['text']

def send_to_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHANNEL_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    return requests.post(url, json=payload).json()

def main():
    post_text = get_random_post()
    if post_text:
        res = send_to_telegram(post_text)
        print("Posted:", res)
    else:
        print("No posts in bank!")

if __name__ == "__main__":
    main()
