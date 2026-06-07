"""
WordPress自動投稿モジュール
生成した記事をWordPress REST APIで直接投稿する
"""

import os
import re
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

WP_URL = os.environ.get("WP_URL", "https://money-compass.jp")
WP_USER = os.environ.get("WP_USER", "mc_admin")
WP_APP_PASSWORD = os.environ.get("WP_APP_PASSWORD", "")


def post_to_wordpress(keyword: str, html_content: str) -> dict:
    """生成した記事をWordPressに投稿する"""

    # タイトルをキーワードから生成
    title = f"{keyword}おすすめ比較ランキング【{_current_year()}年最新】"

    # HTMLからテキスト部分を抽出（WordPressのcontentに使用）
    content = html_content

    # スラッグ（URL）を生成
    slug = re.sub(r"[^\w\s-]", "", keyword).strip().replace(" ", "-")

    api_url = f"{WP_URL}/wp-json/wp/v2/posts"

    payload = {
        "title": title,
        "content": content,
        "status": "publish",
        "slug": slug,
        "categories": [],
        "tags": [],
    }

    response = requests.post(
        api_url,
        json=payload,
        auth=(WP_USER, WP_APP_PASSWORD),
        timeout=30,
    )

    if response.status_code in (200, 201):
        data = response.json()
        print(f"[WP投稿] 完了: {data.get('link')}")
        return {"status": "success", "url": data.get("link"), "id": data.get("id")}
    else:
        print(f"[WP投稿] エラー: {response.status_code} - {response.text[:200]}")
        return {"status": "error", "code": response.status_code, "message": response.text[:200]}


def _current_year() -> str:
    from datetime import datetime
    return datetime.now().strftime("%Y")


if __name__ == "__main__":
    # テスト投稿
    test_html = "<p>これはテスト記事です。自動投稿の動作確認用。</p>"
    result = post_to_wordpress("カードローン テスト", test_html)
    print(result)