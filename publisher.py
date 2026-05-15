import os
import requests
from datetime import datetime
from pathlib import Path

HATENA_ID  = os.environ.get("HATENA_ID", "haruharu_rl")
HATENA_KEY = os.environ.get("HATENA_API_KEY")
BLOG_ID    = os.environ.get("HATENA_BLOG_ID", "haruharu-rl.hatenablog.com")

CTA = "\n\n---\n\n## 今すぐITスキルを身につけるなら\n\n- [TECH CAMP](https://tech-camp.in/)\n- [DMM WEBCAMP](https://web-camp.io/)\n- [レバテックキャリア](https://levtech.jp/)\n"

def load_articles():
    d = Path("articles")
    if not d.exists():
        print("articlesフォルダが見つかりません")
        return []
    today = datetime.now().strftime("%Y%m%d")
    files = [f for f in sorted(d.glob("*.md"), reverse=True) if today in f.name]
    print("本日の記事: " + str(len(files)) + "件")
    return files

def parse_article(filepath):
    text = filepath.read_text(encoding="utf-8")
    title = ""
    body_lines = []
    for line in text.splitlines():
        if line.startswith("タイトル:"):
            title = line.replace("タイトル:", "").strip()
        elif not line.startswith("# ") and not line.startswith("タイトル:"):
            body_lines.append(line)
    body = "\n".join(body_lines).strip() + CTA
    return title, body

def post_to_hatena(title, body):
    q = chr(34)
    safe_title = title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    safe_body = body.replace("]]>", "]]]]><![CDATA[>")
    xml = "<" + "?xml version=" + q + "1.0" + q + " encoding=" + q + "utf-8" + q + "?" + ">"
    xml += "<entry xmlns=" + q + "http://www.w3.org/2005/Atom" + q + " xmlns:app=" + q + "http://www.w3.org/2007/app" + q + ">"
    xml += "<title>" + safe_title + "</title>"
    xml += "<author><name>" + HATENA_ID + "</name></author>"
    xml += "<content type=" + q + "text/x-markdown" + q + "><![CDATA[" + safe_body + "]]></content>"
    xml += "<app:control><app:draft>no</app:draft></app:control>"
    xml += "</entry>"
    endpoint = "https://blog.hatena.ne.jp/" + HATENA_ID + "/" + BLOG_ID + "/atom/entry"
    res = requests.post(endpoint, data=xml.encode("utf-8"), headers={"Content-Type": "application/xml"}, auth=(HATENA_ID, HATENA_KEY), timeout=30)
    if res.status_code == 201:
        print("投稿成功!")
        return True
    else:
        print("投稿失敗: " + str(res.status_code))
        print(res.text[:300])
        return False

def main():
    if not HATENA_KEY:
        print("HATENA_API_KEY が未設定です")
        return
    articles = load_articles()
    if not articles:
        print("本日の記事が見つかりません")
        return
    for filepath in articles:
        print("投稿中: " + filepath.name)
        title, body = parse_article(filepath)
        if not title:
            title = filepath.stem.replace("_", " ")
        post_to_hatena(title, body)
    print("全記事投稿完了!")

main()
