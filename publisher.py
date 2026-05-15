import os
import requests
from datetime import datetime
from pathlib import Path

HATENA_ID        = os.environ.get("HATENA_ID", "haruharu_rl")
HATENA_KEY       = os.environ.get("HATENA_API_KEY")
BLOG_ID          = os.environ.get("HATENA_BLOG_ID", "haruharu-rl.hatenablog.com")
UNSPLASH_KEY     = os.environ.get("UNSPLASH_ACCESS_KEY")

CTA = "\n\n---\n\n## ???IT???????????\n\n- [TECH CAMP](https://tech-camp.in/)\n- [DMM WEBCAMP](https://web-camp.io/)\n- [?????????](https://levtech.jp/)\n"

def get_image_url(keyword):
    if not UNSPLASH_KEY:
        return None
    try:
        r = requests.get("https://api.unsplash.com/photos/random", params={"query": keyword, "orientation": "landscape"}, headers={"Authorization": "Client-ID " + UNSPLASH_KEY}, timeout=10)
        if r.status_code == 200:
            return r.json()["urls"]["regular"]
    except Exception as e:
        print("???????: " + str(e))
    return None

def load_articles():
    d = Path("articles")
    if not d.exists():
        print("articles????????????")
        return []
    today = datetime.now().strftime("%Y%m%d")
    files = [f for f in sorted(d.glob("*.md"), reverse=True) if today in f.name]
    print("?????: " + str(len(files)) + "?")
    return files

def parse_article(filepath):
    text = filepath.read_text(encoding="utf-8")
    title = ""
    body_lines = []
    for line in text.splitlines():
        if line.startswith("????:"):
            title = line.replace("????:", "").strip()
        elif not line.startswith("# ") and not line.startswith("????:"):
            body_lines.append(line)
    body = "\n".join(body_lines).strip() + CTA
    return title, body

def add_image_to_body(body, image_url):
    if not image_url:
        return body
    img_md = "\n\n![](" + image_url + ")\n\n"
    lines = body.split("\n")
    result = []
    img_inserted = False
    for line in lines:
        result.append(line)
        if not img_inserted and line.startswith("## "):
            result.append(img_md)
            img_inserted = True
    if not img_inserted:
        result.insert(0, img_md)
    return "\n".join(result)

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
        print("????!")
        return True
    else:
        print("????: " + str(res.status_code))
        print(res.text[:300])
        return False

def main():
    if not HATENA_KEY:
        print("HATENA_API_KEY ??????")
        return
    articles = load_articles()
    if not articles:
        print("?????????????")
        return
    for filepath in articles:
        print("???: " + filepath.name)
        title, body = parse_article(filepath)
        if not title:
            title = filepath.stem.replace("_", " ")
        image_url = get_image_url("programming technology engineer")
        if image_url:
            print("??????!")
            body = add_image_to_body(body, image_url)
        post_to_hatena(title, body)
    print("???????!")

main()
