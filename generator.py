import json
import os
import re
import time
from datetime import datetime
from pathlib import Path
from google import genai

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

def load_latest_data():
    files = sorted(Path(".").glob("raw_data_*.json"), reverse=True)
    if not files:
        print("収集データが見つかりません")
        return []
    with open(files[0], encoding="utf-8") as f:
        return json.load(f)

def generate_article(post, retries=5, wait=60):
    prompt = (
        "あなたはIT転職・プログラミング学習専門のブログライターです。\n"
        "以下の海外エンジニアコミュニティの投稿をもとに、日本人読者向けのSEO記事を日本語で書いてください。\n\n"
        "【元投稿タイトル】" + post["title"] + "\n"
        "【元投稿内容】" + post["body"][:300] + "\n"
        "【スコア】" + str(post["score"]) + "\n"
        "【出典】" + post["url"] + "\n\n"
        "【記事の要件】\n"
        "- 文字数: 2000〜2500字\n"
        "- 導入文は3行以内で「この記事でわかること」を明示すること\n"
        "- 導入文の直後に [:contents] と記載して目次を設置すること\n"
        "- ## や ### の見出しを使って4〜5セクションに構造化すること\n"
        "- 箇条書きは - を使うこと（* は使わない）\n"
        "- 重要なキーワードや結論は **太字** にすること\n"
        "- 特に重要なキーワード（記事のコアとなる3〜5語）は キーワード で囲むこと\n"
        "- 重要なリストやまとめ部分は 
 と 
 で囲んで囲み枠にすること\n"
        "- 2〜3行ごとに空行を入れてスマホでも読みやすくすること\n"
        "- 各段落は短めに（4行以内）まとめること\n"
        "- 海外エンジニアのリアルな声として元投稿を引用すること\n"
        "- Markdownとして正しく整形すること\n"
        "- プログラミングスクール（TECH CAMP、DMM WEBCAMP等）への自然な誘導文をCTAとして最後に追加\n\n"
        "【出力形式】\n"
        "タイトル: （SEOタイトル）\n"
        "---\n"
        "（導入文3行以内）\n\n"
        "[:contents]\n\n"
        "## （見出し）\n"
        "（本文）"
    )
    for attempt in range(1, retries + 1):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            return response.text
        except Exception as e:
            msg = str(e)
            if "503" in msg or "UNAVAILABLE" in msg or "429" in msg or "EXHAUSTED" in msg:
                print("  エラー（試行" + str(attempt) + "/" + str(retries) + "）: " + str(wait) + "秒待ってリトライします...")
                time.sleep(wait)
            else:
                print("  生成エラー: " + msg)
                return None
    print("  リトライ上限に達しました。スキップします。")
    return None

def save_article(post, content):
    articles_dir = Path("articles")
    articles_dir.mkdir(exist_ok=True)
    date_str = datetime.now().strftime("%Y%m%d")
    safe_title = re.sub(r"[^\w]", "_", post["title"][:30])
    filename = articles_dir / (date_str + "_" + safe_title + ".md")
    with open(filename, "w", encoding="utf-8") as f:
        f.write("# 元ネタ: " + post["title"] + "\n")
        f.write("# 出典: " + post["url"] + "\n")
        f.write("# スコア: " + str(post["score"]) + "\n\n")
        f.write(content)
    print("  保存: " + str(filename))
    return filename

def main():
    posts = load_latest_data()
    if not posts:
        return
    top_posts = posts[:3]
    print("上位" + str(len(top_posts)) + "件の投稿から記事を生成します")
    for i, post in enumerate(top_posts, 1):
        print("\n[" + str(i) + "/" + str(len(top_posts)) + "] 生成中: " + post["title"][:50] + "...")
        content = generate_article(post)
        if content:
            save_article(post, content)
            print("  完了!")
        else:
            print("  スキップ")
    print("\n全記事生成完了!")

main()