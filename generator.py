import json
import os
import re
from datetime import datetime
from pathlib import Path
from google import genai

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

# 使えるモデルを確認
print("=== 使用可能なモデル一覧 ===")
for m in client.models.list():
    if "gemini" in m.name.lower():
        print(m.name)