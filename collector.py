import requests
import json
from datetime import datetime

SUBREDDITS = [
    "cscareerquestions",
    "learnprogramming",
    "webdev",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 ArticleCollector/1.0"
}

def fetch_reddit_hot(subreddit, limit=5):
    url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit={limit}"
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        res.raise_for_status()
        data = res.json()
        posts = []
        for post in data["data"]["children"]:
            p = post["data"]
            if p["score"] < 50:
                continue
            posts.append({
                "title":     p["title"],
                "score":     p["score"],
                "comments":  p["num_comments"],
                "url":       f"https://reddit.com{p['permalink']}",
                "body":      p.get("selftext", "")[:500],
                "subreddit": subreddit,
                "collected": datetime.now().isoformat()
            })
        return posts
    except Exception as e:
        print(f"エラー ({subreddit}): {e}")
        return []

def collect_all():
    all_posts = []
    for sub in SUBREDDITS:
        print(f"収集中: r/{sub}")
        posts = fetch_reddit_hot(sub)
        all_posts.extend(posts)
        print(f"  → {len(posts)}件取得")
    all_posts.sort(key=lambda x: x["score"], reverse=True)
    filename = f"raw_data_{datetime.now().strftime('%Y%m%d')}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(all_posts, f, ensure_ascii=False, indent=2)
    print(f"\n完了！ {len(all_posts)}件を {filename} に保存")
    for p in all_posts[:3]:
        print(f"  [{p['score']}] {p['title'][:60]}...")
    return all_posts

posts = collect_all()
