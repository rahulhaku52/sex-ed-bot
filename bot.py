import os, requests
from openai import OpenAI

BOT_TOKEN = os.environ['BOT_TOKEN']
CHANNEL_ID = os.environ['CHANNEL_ID']
DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY')

deepseek = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

TOPICS = [
    "কনডম ব্যবহারের সঠিক নিয়ম ও ভুল ধারণা",
    "সম্মতি (Consent) কী ও কেন জরুরি",
    "পিরিয়ড বা মাসিক চক্র সম্পর্কে সঠিক তথ্য",
    "যৌন সংক্রমণ (STI) প্রতিরোধের উপায়",
    "বয়ঃসন্ধিকালে শরীরের পরিবর্তন",
    "নিরাপদ যৌনতা (Safe Sex) কী",
    "সম্পর্কের মূল ভিত্তি: বিশ্বাস ও শ্রদ্ধা",
    "মাস্টারবেশন নিয়ে ভুল ধারণা ও সত্য",
    "জন্মনিয়ন্ত্রণ পদ্ধতি সম্পর্কে জানা",
    "LGBTQIA+ কমিউনিটি বোঝা",
    "মানসিক স্বাস্থ্য ও যৌনতা",
    "প্রথম যৌন সম্পর্কের আগে যে বিষয়গুলো জানা জরুরি",
    "যৌন নিপীড়ন (Sexual Harassment) কী ও প্রতিকার",
    "নারীর যৌন স্বাস্থ্য",
    "পুরুষের যৌন স্বাস্থ্য",
]

def generate_bangla_post(topic):
    prompt = f"""তুমি একজন অভিজ্ঞ যৌনশিক্ষা বিশেষজ্ঞ। নিচের টপিক নিয়ে বাংলায় একটি সুন্দর, সহজ, গল্পের মতো শিক্ষামূলক পোস্ট লেখো।

টপিক: {topic}

গুরুত্বপূর্ণ নির্দেশনা:
- সম্পূর্ণ বাংলায় লিখবে, কোনো ইংরেজি শব্দ ব্যবহার করবে না (শুধু কনডম, STI, HIV ইত্যাদি চিকিৎসা শব্দ ছাড়া)
- লেখার ধরন হবে বন্ধুর সাথে কথা বলার মতো, সহজ ও উষ্ণ
- কোনো "হ্যালো", "বাই", "গাইজ" ইত্যাদি অপ্রয়োজনীয় শব্দ ব্যবহার করবে না
- পোস্ট সম্পূর্ণ করবে, শেষ বাক্য অসম্পূর্ণ রাখবে না
- হ্যাশট্যাগ দেবে: #SexEducation #শিক্ষা #স্বাস্থ্য
- ন্যূনতম ৩০০ শব্দ লিখবে"""

    response = deepseek.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
        max_tokens=2000
    )
    return response.choices[0].message.content.strip()

def send_to_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    return requests.post(url, json={
        "chat_id": CHANNEL_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }).json()

def main():
    import random
    topic = random.choice(TOPICS)
    print(f"📝 Generating post on: {topic}")
    
    post = generate_bangla_post(topic)
    res = send_to_telegram(post)
    
    if res.get('ok'):
        print("✅ Post sent successfully!")
    else:
        print("❌ Failed:", res)

if __name__ == "__main__":
    main()
