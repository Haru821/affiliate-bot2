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
        "あなたはIT転職・プログラミング学習ブログの専門ライターです。\n"
        "以下の海外エンジニアの投稿をヒントに、"
        "「プログラミング未経験・IT転職を検討している20〜35歳の日本人」"
        "が検索・共感する日本語SEO記事を書いてください。\n\n"
        "【元投稿タイトル】" + post["title"] + "\n"
        "【元投稿内容】" + post["body"][:300] + "\n\n"
        "【ターゲット読者】\n"
        "- 今の仕事に不満があり転職を考えている非エンジニア\n"
        "- プログラミングを学びたいが何から始めるか迷っている未経験者\n"
        "- 30代でエンジニア転職できるか不安な人\n\n"
        "【記事の方向性】\n"
        "元投稿のテーマを活かしつつ、以下のような切り口で記事化する:\n"
        "- 「未経験からエンジニアになった人の実例・声」\n"
        "- 「プログラミングスクールは意味ある？現実を解説」\n"
        "- 「30代・文系でもエンジニア転職できる理由」\n"
        "- 「独学 vs スクール どちらが転職に有利か」\n"
        "- 「エンジニア転職で年収はどう変わるか」\n"
        "※ 元投稿と完全に同じテーマでなくてよい。転職・学習に自然につながる記事にすること。\n\n"
        "【要件】\n"
        "- 2000-2500字\n"
        "- 導入文3行以内で「この記事でわかること」を明示\n"
        "- 導入文の直後に、他のテキストと混ぜずに必ず単独行で [:contents] とだけ書くこと\n"
        "- ## ### で4-5セクション構造化\n"
        "- 箇条書きは - を使う\n"
        "- 重要キーワードは **太字**\n"
        + req1 + req2 +
        "- <div class=\"box\">と</div>は必ず単独行に書くこと。囲んだ中身はMarkdownのリスト形式で書くこと\n"
        "- 2-3行ごとに空行\n"
        "- 各段落4行以内\n"
        "- 実際に転職した人のリアルなエピソードや声を盛り込む\n"
        "- 読者の不安・悩みに寄り添うトーン\n"
        "- 最後のセクションでプログラミングスクールへの自然な誘導文を書く\n\n"
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
                print("  error (skip): " + msg)
                return None
    print("  retry exhausted: gave up after " + str(retries) + " retries")
    return None

def fix_contents_tag(content):
    content = re.sub(r'\[:contents\]', '', content)
    lines = content.splitlines()
    result = []
    inserted = False
    for line in lines:
        if not inserted and line.startswith("## "):
            result.append("")
            result.append("[:contents]")
            result.append("")
            inserted = True
        result.append(line)
    if not inserted:
        result.insert(0, "[:contents]\n")
    return "\n".join(result)

def save_article(post, content):
    articles_dir = Path("articles")
    articles_dir.mkdir(exist_ok=True)
    date_str = datetime.now().strftime("%Y%m%d")
    safe_title = re.sub(r"[^\w]", "_", post["title"][:30])
    filename = articles_dir / (date_str + "_" + safe_title + ".md")
    content = fix_contents_tag(content)
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
