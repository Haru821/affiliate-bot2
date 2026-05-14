import requests
import json
from datetime import datetime

HEADERS = {"User-Agent": "Mozilla/5.0 ArticleCollector/1.0"}

KEYWORDS = [
    "career", "job", "hiring", "layoff", "engineer",
    "programming", "bootcamp", "learn", "salary", "remote"
]

def fetch_hn_top_stories(limit=30):
    url = "https://hacker-news.firebaseio.com/v0/topstories.json"
    res = requests.get(url, headers=HEADERS, timeout=10)
    return res.json()[:limit]

def fetch_story(story_id):
    url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
    res = requests.get(url, headers=HEADERS, timeout=10)
    return res.json()

def is_relevant(story):
    text = (story.get("title", "") + " " + story.get("text", "")).lower()
    return any(kw in text for kw in KEYWORDS)

def collect_all():
    print("Hacker News からトップ記事を収集中...")
    story_ids = fetch_hn_top_stories(limit=50)
    
    posts = []
    for sid in story_ids:
        try:
            story = fetch_story(sid)
            if not story or story.get("type") != "story":
                continue
            if story.get("score", 0) < 10:
                continue
            if not is_relevant(story):
                continue
            posts.append({
                "title":     story.get("title", ""),
                "score":     story.get("score", 0),
                "comments":  story.get("descendants", 0),
                "url":       story.get("url", f"https://news.ycombinator.com/item?id={sid}"),
                "body":      story.get("text", "")[:500],
                "source":    "hackernews",
                "collected": datetime.now().isoformat()
            })
        except Exception as e:
            print(f"  スキップ: {e}")
            continue

    posts.sort(key=lambda x: x["score"], reverse=True)
    filename = f"raw_data_{datetime.now().strftime('%Y%m%d')}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)

    print(f"\n完了！ {len(posts)}件を {filename} に保存")
    for p in posts[:3]:
        print(f"  [{p['score']}点] {p['title'][:60]}")
    return posts

collect_all()
