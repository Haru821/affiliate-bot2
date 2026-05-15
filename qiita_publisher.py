import os
import requests
import json
from datetime import datetime
from pathlib import Path

QIITA_TOKEN = os.environ.get("QIITA_ACCESS_TOKEN")

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
    body_lines = []
    for line in text.splitlines():
        if line.startswith("タイトル:"):
            title = line.replace("タイトル:", "").strip()
        elif not line.startswith("# "):
            body_lines.append(line)
    body = "\n".join(body_lines).strip()
    return title, body

def post_to_qiita(title, body):
    if not title:
        print("title not found")
        return False

    headers = {
        "Authorization": "Bearer " + QIITA_TOKEN,
        "Content-Type": "application/json"
    }
    data = {
        "title": title,
        "body": body,
        "private": False,
        "tags": [
            {"name": "プログラミング", "versions": []},
            {"name": "IT転職", "versions": []},
            {"name": "未経験", "versions": []},
            {"name": "転職", "versions": []},
            {"name": "エンジニア", "versions": []}
        ]
    }
    res = requests.post(
        "https://qiita.com/api/v2/items",
        headers=headers,
        data=json.dumps(data),
        timeout=30
    )
    if res.status_code == 201:
        url = res.json().get("url", "")
        print("posted: " + url)
        return True
    else:
        print("error: " + str(res.status_code))
        print(res.text[:300])
        return False

def main():
    if not QIITA_TOKEN:
        print("QIITA_ACCESS_TOKEN not set")
        return

    articles = load_articles()
    if not articles:
        print("no articles today")
        return

    for filepath in articles:
        print("posting: " + filepath.name)
        title, body = parse_article(filepath)
        post_to_qiita(title, body)

    print("complete!")

main()
