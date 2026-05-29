import os
import json
import random
import requests

BOT_TOKEN = os.environ['BOT_TOKEN']
CHANNEL_ID = os.environ['CHANNEL_ID']

def send_to_telegram(text):
    """টেলিগ্রাম চ্যানেলে মেসেজ পাঠানোর ফাংশন"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHANNEL_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    response = requests.post(url, json=payload)
    return response.json()

def main():
    try:
        # posts.json ফাইল থেকে পোস্ট লোড করা
        with open('posts.json', 'r', encoding='utf-8') as f:
            posts = json.load(f)

        if not posts:
            print("⚠️ posts.json ফাইলটি খালি! অনুগ্রহ করে কিছু পোস্ট যোগ করুন।")
            return

        # একটি র‌্যান্ডম পোস্ট নির্বাচন
        random_post = random.choice(posts)
        post_text = random_post['text']

        # টেলিগ্রামে পাঠানো
        result = send_to_telegram(post_text)

        if result.get('ok'):
            print("✅ পোস্ট সফলভাবে চ্যানেলে পাঠানো হয়েছে।")
        else:
            print(f"❌ পোস্ট ব্যর্থ হয়েছে। এরর: {result}")

    except FileNotFoundError:
        print("❌ posts.json ফাইলটি রিপোজিটরিতে পাওয়া যায়নি। দয়া করে ফাইলটি তৈরি করুন।")
    except json.JSONDecodeError:
        print("❌ posts.json ফাইলের ফরম্যাট সঠিক নয়। JSON সিনট্যাক্স চেক করুন।")
    except Exception as e:
        print(f"❌ অপ্রত্যাশিত ত্রুটি: {e}")

if __name__ == "__main__":
    main()
