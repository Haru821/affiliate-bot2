import json
import os
import re
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

def generate_article(post):
    prompt = f"""
あなたはIT転職・プログラミング学習専門のブログライターです。
以下の海外エンジニアコミュニティの投稿をもとに、日本人読者向けの
SEO記事を日本語で書いてください。

【元投稿タイトル】{post['title']}
【元投稿内容】{post['body'][:300]}
【スコア】{post['score']}
【出典】{post['url']}

【記事の要件】
- 文字数: 1500〜2000字
- H2見出し3〜4個
- 「海外エンジニアのリアルな声」として元投稿を引用
- 日本のプログラミングスクール（TECH CAMP、DMM WEBCAMP等）への
  自然な誘導文をCTAとして最後に追加
- 「このスキルを学ぶならプログラミングスクールの無料カウンセリングがおすすめ」
  という流れでアフィリエイト誘導

【出力形式】
タイトル: （SEOタイトル）
---
（本文）
"""
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        return response.text
    except Exception as e:
        print(f"生成エラー: {e}")
        return None

def save_article(post, content):
    articles_dir = Path("articles")
    articles_dir.mkdir(exist_ok=True)
    date_str = datetime.now().strftime("%Y%m%d")
    safe_title = re.sub(r'[^\w]', '_', post['title'][:30])
    filename = articles_dir / f"{date_str}_{safe_title}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# 元ネタ: {post['title']}\n")
        f.write(f"# 出典: {post['url']}\n")
        f.write(f"# スコア: {post['score']}\n\n")
        f.write(content)
    print(f"保存: {filename}")
    return filename

def main():
    posts = load_latest_data()
    if not posts:
        return
    top_posts = posts[:3]
    print(f"上位{len(top_posts)}件の投稿から記事を生成します")
    for i, post in enumerate(top_posts, 1):
        print(f"\n[{i}/{len(top_posts)}] 生成中: {post['title'][:50]}...")
        content = generate_article(post)
        if content:
            save_article(post, content)
            print(f"  完了!")
        else:
            print(f"  スキップ")
    print("\n全記事生成完了!")

main()