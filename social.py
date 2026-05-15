import os
import requests
import json
from datetime import datetime
from pathlib import Path
from requests_oauthlib import OAuth1

CONSUMER_KEY = os.environ.get("X_CONSUMER_KEY")
CONSUMER_SECRET = os.environ.get("X_CONSUMER_SECRET")
ACCESS_TOKEN = os.environ.get("X_ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.environ.get("X_ACCESS_TOKEN_SECRET")
BLOG_URL = "https://haruharu-rl.hatenablog.com"

def load_articles():
    d = Path("articles")
    if not d.exists():
        print("articles not found")
        return []
    today = datetime.now().strftime("%Y%m%d")
    files = [f for f in sorted(d.glob("*.md"), reverse=True) if today in f.name]
    print("articles: " + str(len(files)))
    return files

def parse_article(filepath):
    text = filepath.read_text(encoding="utf-8")
    title = ""
    for line in text.splitlines():
        if line.startswith("タイトル:"):
            title = line.replace("タイトル:", "").strip()
            break
    return title

def post_tweet(text):
    auth = OAuth1(CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    res = requests.post(
        "https://api.twitter.com/2/tweets",
        auth=auth,
        json={"text": text},
        headers={"Content-Type": "application/json"}
    )
    if res.status_code == 201:
        data = res.json()
        print("posted: " + data["data"]["id"])
        return data["data"]["id"]
    else:
        print("error: " + str(res.status_code))
        print(res.text[:200])
        return None

def reply_tweet(tweet_id, text):
    auth = OAuth1(CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    res = requests.post(
        "https://api.twitter.com/2/tweets",
        auth=auth,
        json={"text": text, "reply": {"in_reply_to_tweet_id": tweet_id}},
        headers={"Content-Type": "application/json"}
    )
    if res.status_code == 201:
        print("replied!")
        return True
    else:
        print("reply error: " + str(res.status_code))
        return False

def main():
    if not CONSUMER_KEY:
        print("X_CONSUMER_KEY not set")
        return

    articles = load_articles()
    if not articles:
        print("no articles today")
        return

    filepath = articles[0]
    title = parse_article(filepath)
    if not title:
        title = filepath.stem.replace("_", " ")

    tweet1 = (
        "【IT転職・プログラミング学習】\n\n"
        + title + "\n\n"
        + "#プログラミング #IT転職 #未経験エンジニア #転職"
    )

    tweet_id = post_tweet(tweet1)

    if tweet_id:
        tweet2 = "続きはブログで読めます👇\n" + BLOG_URL
        reply_tweet(tweet_id, tweet2)

    print("complete!")

main()
