import os
import json
import requests
import hashlib
import base64
from datetime import datetime
from pathlib import Path
import xml.etree.ElementTree as ET

HATENA_ID  = os.environ.get("HATENA_ID", "haruharu_rl")
HATENA_KEY = os.environ.get("HATENA_API_KEY")
BLOG_ID    = os.environ.get("HATENA_BLOG_ID", "haruharu-rl.hatenablog.com")

AFFILIATE_LINKS = {
    "TECHCAMP":   "https://tech-camp.in/",
    "DMMWEBCAMP": "https://web-camp.io/",
    "LEVTECH":    "https://levtech.jp/",
}

def get_cta():
    return """
---

## 今すぐITスキルを身につけるなら

海外エンジニアのリアルな声からもわかるように、ITスキルの需要は今後も高まり続けます。
まずは無料カウンセリングで自分に合ったスクールを探してみましょう。

- [TECH CAMP - 無料カウンセリングはこちら]({TECHCAMP})
- [DMM WEBCAMP - まず話を聞いてみる]({DMMWEBCAMP})
- [レバテックキャリア - IT転職を相談する]({LEVTECH})
""".format(**AFFILIATE_LINKS)

def build_wsse(username, api_key):
    import random, string
    from datetime import timezone
    nonce_raw = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    nonce = base64.b64encode(nonce_raw.encode()).decode()
    created = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    digest = base64.b64encode(
        hashlib.sha1((nonce_raw + created + api_key).encode()).digest()
    ).decode()
    return f'UsernameToken Username="{username}", PasswordDigest="{digest}", Nonce="{nonce}", Created="{created}"'

def load_articles():
    articles_dir = Path("articles")
    if not articles_dir.exists():
        print("articlesフォルダが見つかりません")
        return []
    files = sorted(articles_dir.glob("*.md"), reverse=True)
    today = datetime.now().strftime("%Y%m%d")
    return [f for f in files if today in f.name]

def parse_article(filepath):
    with open(filepath, encoding="utf-8") as f:
        lines = f.readlines()
    title = ""
    body_lines = []
    for line in lines:
        if line.startswith("タイトル:"):
            title = line.replace("タイトル:", "").strip()
        elif not line.startswith("# "):
            body_lines.append(line)
    content = "".join(body_lines).strip()
    content += get_cta()
    return title, content

def post_to_hatena(title, content):
    endpoint = f"https://blog.hatena.ne.jp/{HATENA_ID}/{BLOG_ID}/atom/entry"
    wsse = build_wsse(HATENA_ID, HATENA_KEY)
    xml_body = f'''

  
  {HATENA_ID}
  {content}
  no
'''
    headers = {
        "X-WSSE": wsse,
        "Content-Type": "application/xml",
    }
    res = requests.post(endpoint, data=xml_body.encode("utf-8"), headers=headers, timeout=30)
    if res.status_code == 201:
        root = ET.fromstring(res.text)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        link = root.find("atom:link[@rel='alternate']", ns)
        url = link.attrib["href"] if link is not None else "URL不明"
        print(f"投稿成功: {url}")
        return True
    else:
        print(f"投稿失敗: {res.status_code}")
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
    print(f"{len(articles)}件の記事を投稿します")
    for filepath in articles:
        print(f"\n投稿中: {filepath.name}")
        title, content = parse_article(filepath)
        if not title:
            title = filepath.stem.replace("_", " ")
        post_to_hatena(title, content)
    print("\n全記事投稿完了!")

main()