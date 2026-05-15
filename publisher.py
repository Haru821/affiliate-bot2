import os
import requests
import hashlib
import base64
import random
import string
from datetime import datetime, timezone
from pathlib import Path

HATENA_ID  = os.environ.get("HATENA_ID", "haruharu_rl")
HATENA_KEY = os.environ.get("HATENA_API_KEY")
BLOG_ID    = os.environ.get("HATENA_BLOG_ID", "haruharu-rl.hatenablog.com")

CTA = "\n\n---\n\n## 今すぐITスキルを身につけるなら\n\n- [TECH CAMP](https://tech-camp.in/)\n- [DMM WEBCAMP](https://web-camp.io/)\n- [レバテックキャリア](https://levtech.jp/)\n"

def build_wsse():
    nonce_raw = "".join(random.choices(string.ascii_letters + string.digits, k=16))
    nonce = base64.b64encode(nonce_raw.encode()).decode()
    created = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    digest = base64.b64encode(hashlib.sha1((nonce_raw + created + HATENA_KEY).encode()).digest()).decode()
    return 'UsernameToken Username="' + HATENA_ID + '", PasswordDigest="' + digest + '", Nonce="' + nonce + '", Created="' + created + '"'

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
        elif not line.startswith("# "):
            body_lines.append(line)
    body = "\n".join(body_lines).strip() + CTA
    return title, body

def post_to_hatena(title, body):
    endpoint = "https://blog.hatena.ne.jp/" + HATENA_ID + "/" + BLOG_ID + "/atom/entry"
    safe_title = title.replace("&", "&").replace("<", "<").replace(">", ">")
    safe_body = body.replace("]]>", "]]]]>")
    lines = [
        '',
        '',
        '  ',
        '  ' + HATENA_ID + '',
        '  ',
        '  no',
        '',
    ]
    xml = "\n".join(lines)
    print("送信XML先頭: " + xml[:100])
    headers = {
        "X-WSSE": build_wsse(),
        "Content-Type": "application/xml; charset=utf-8",
    }
    res = requests.post(endpoint, data=xml.encode("utf-8"), headers=headers, timeout=30)
    if res.status_code == 201:
        print("投稿成功!")
        return True
    else:
        print("投稿失敗: " + str(res.status_code))
        print(res.text[:500])
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