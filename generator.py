import json, os, re, time
from datetime import datetime
from pathlib import Path
from google import genai

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

def load_latest_data():
    files = sorted(Path(".").glob("raw_data_*.json"), reverse=True)
    if not files:
        print("data not found")
        return []
    with open(files[0], encoding="utf-8") as f:
        return json.load(f)

def generate_article(post, retries=5, wait=60):
    req1 = "- 重要なキーワードは <mark>キーワード</mark> で囲むこと\n"
    req2 = "- 重要なリスト部分は <div class=\"box\"> と </div> で囲むこと\n"
    prompt = (
        "IT転職・プログラミング学習専門のブログライターとして日本語SEO記事を書いてください。\n\n"
        "【元投稿タイトル】" + post["title"] + "\n"
        "【元投稿内容】" + post["body"][:300] + "\n"
        "【スコア】" + str(post["score"]) + "\n"
        "【出典】" + post["url"] + "\n\n"
        "【要件】\n"
        "- 2000-2500字\n"
        "- 導入文3行以内で記事でわかることを明示\n"
        "- 導入文直後に [:contents] を記載\n"
        "- ## ### で4-5セクション構造化\n"
        "- 箇条書きは - を使う\n"
        "- 重要キーワードは **太字**\n"
        + req1 + req2 +
        "- 2-3行ごとに空行\n"
        "- 各段落4行以内\n"
        "- 海外エンジニアの声を引用\n"
        "- 最後にTECH CAMP等へのCTAを追加\n\n"
        "【形式】\nタイトル: (SEOタイトル)\n---\n(本文)"
    )
    for attempt in range(1, retries + 1):
        try:
            response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
            return response.text
        except Exception as e:
            msg = str(e)
            if "503" in msg or "UNAVAILABLE" in msg or "429" in msg or "EXHAUSTED" in msg:
                print("  retry " + str(attempt) + "/" + str(retries) + " wait " + str(wait) + "s...")
                time.sleep(wait)
            else:
                print("  error: " + msg)
                return None
    return None

def save_article(post, content):
    articles_dir = Path("articles")
    articles_dir.mkdir(exist_ok=True)
    date_str = datetime.now().strftime("%Y%m%d")
    safe_title = re.sub(r"[^\w]", "_", post["title"][:30])
    filename = articles_dir / (date_str + "_" + safe_title + ".md")
    with open(filename, "w", encoding="utf-8") as f:
        f.write("# " + post["title"] + "\n")
        f.write("# " + post["url"] + "\n")
        f.write("# " + str(post["score"]) + "\n\n")
        f.write(content)
    print("  saved: " + str(filename))
    return filename

def main():
    posts = load_latest_data()
    if not posts:
        return
    top_posts = posts[:3]
    print("generating " + str(len(top_posts)) + " articles")
    for i, post in enumerate(top_posts, 1):
        print("\n[" + str(i) + "/" + str(len(top_posts)) + "] " + post["title"][:50])
        content = generate_article(post)
        if content:
            save_article(post, content)
            print("  done!")
        else:
            print("  skip")
    print("\ncomplete!")

main()
