"""
WRITE班 — 記事自動生成エンジン
マネーコンパス株式会社

使い方:
  python auto_writer.py "カードローン 審査 甘い"
  python auto_writer.py --all   # キーワードリストから全部生成
"""

import anthropic
import os
import json
import re
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from wp_poster import post_to_wordpress

# .envファイルからAPIキーを自動読み込み
load_dotenv(Path(__file__).parent.parent / ".env")
API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# カテゴリ判定キーワード
CATEGORY_RULES = {
    "stocks":   ["NISA", "nisa", "iDeCo", "ideco", "株", "証券", "ETF", "投資信託", "配当", "米国株", "S&P"],
    "setsuzei": ["節税", "会社設立", "法人", "確定申告", "ふるさと納税", "役員報酬", "経費", "副業", "法人成り"],
}

def detect_category(keyword: str) -> str:
    for cat, words in CATEGORY_RULES.items():
        if any(w in keyword for w in words):
            return cat
    return "cardloan"

# カテゴリ別アフィリエイトリンク
AFFILIATE_LINKS = {
    "cardloan": {
        "セントラル": "https://px.a8.net/svt/ejp?a8mat=4B5Q85+2HB1IQ+363I+64C3M",
        "資金調達プロ": "https://px.a8.net/svt/ejp?a8mat=4B5Q85+39VUK2+40JM+TYJ5U",
        "アコム":   "",
        "プロミス": "",
        "アイフル": "",
        "レイク":   "",
        "モビット": "",
    },
    "stocks": {
        "楽天証券": "",  # 提携申請後に追加
        "SBI証券":  "",  # 提携申請後に追加
        "松井証券": "",
        "マネックス証券": "",
    },
    "setsuzei": {
        "freee": "",      # 会計ソフト
        "マネーフォワード": "",
        "弥生会計": "",
    },
}

# 出力先
OUTPUT_DIR = Path(__file__).parent.parent / "articles" / "generated"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ==========================================
# 記事生成エンジン（WRITE班の中枢）
# ==========================================
SYSTEM_PROMPTS = {
    "cardloan": """あなたはマネーコンパス株式会社のWRITE班AIです。
カードローン・消費者金融専門の金融情報メディア記事を生成します。

【必ず守るルール】
- 「必ず審査通過」「審査なし保証」等の断定表現を使わない（景表法違反）
- アフィリエイトリンクは必ず「広告」「PR」と明記する
- 金利・条件は「2026年現在」と時点を明記する
- 文字数：2,500〜3,500文字・HTML形式で出力する
- 執筆者は「田中誠一（元メガバンク融資審査担当・FP1級）」

【記事構成】
1. 導入リード文（200字）
2. H2「〇〇ランキング TOP5」+ 比較テーブル
3. H2「選ぶときの注意点」
4. H2「よくある質問（Q&A）」3問
5. まとめ・CTA（アフィリエイトリンク）
""",

    "stocks": """あなたはマネーコンパス株式会社のWRITE班AIです。
株式投資・NISA・iDeCo・証券口座専門の金融メディア記事を生成します。

【必ず守るルール】
- 「必ず儲かる」「元本保証」等の断定表現を使わない（金融商品取引法）
- 「投資はご自身の判断と責任のもとで行ってください」を必ず記載
- アフィリエイトリンクは必ず「PR」と明記する
- 情報は「2026年現在」と時点を明記する
- 文字数：2,500〜3,500文字・HTML形式で出力する
- 執筆者は「田中誠一（投資歴20年・元銀行資産運用部門・FP1級・証券外務員一種）」

【記事構成】
1. 導入リード文（200字）
2. H2「〇〇おすすめランキング」+ 比較テーブル
3. H2「始め方・手順」
4. H2「注意点・失敗しないコツ」
5. H2「よくある質問（Q&A）」3問
6. まとめ・CTA（証券口座開設アフィリエイトリンク）
""",

    "setsuzei": """あなたはマネーコンパス株式会社のWRITE班AIです。
節税対策・会社設立・法人経営専門の金融メディア記事を生成します。

【必ず守るルール】
- 「必ず節税できる」等の断定を避け「〜の可能性があります」と表現する
- 「税務については税理士にご相談ください」を必ず記載
- アフィリエイトリンクは必ず「PR」と明記する
- 情報は「2026年現在」と時点を明記する
- 文字数：2,500〜3,500文字・HTML形式で出力する
- 執筆者は「田中誠一（元メガバンク融資審査担当22年・法人コンサル80社以上・日商簿記2級・FP1級）」

【記事構成】
1. 導入リード文（200字）
2. H2「〇〇の方法・手順」
3. H2「具体的な節税額シミュレーション」
4. H2「注意点・よくある失敗」
5. H2「よくある質問（Q&A）」3問
6. まとめ・CTA
""",
}


def generate_article(keyword: str) -> dict:
    """キーワードからSEO記事を生成する"""
    client = anthropic.Anthropic(api_key=API_KEY)
    category = detect_category(keyword)
    system_prompt = SYSTEM_PROMPTS[category]
    affiliate_links = AFFILIATE_LINKS[category]

    placeholder_list = " ".join(f"{{{{{k}}}}}" for k in affiliate_links.keys())

    reader_map = {
        "cardloan": "借入を検討している一般の方",
        "stocks":   "投資・資産運用に興味がある方",
        "setsuzei": "節税・法人経営に興味がある方や経営者",
    }

    print(f"[WRITE班] 記事生成開始: {keyword} (カテゴリ: {category})")

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=5000,
        system=system_prompt,
        messages=[{
            "role": "user",
            "content": f"""以下のキーワードでSEO記事を生成してください。

メインキーワード：{keyword}
対象読者：{reader_map[category]}
記事の目的：情報提供 + アフィリエイト誘導

アフィリエイトリンクは {placeholder_list} のプレースホルダーで挿入してください。
HTMLの <article> タグで全体を囲んでください。"""
        }]
    )

    raw_content = message.content[0].text

    article_match = re.search(r"<article>.*?</article>", raw_content, re.DOTALL)
    if article_match:
        raw_content = article_match.group(0)

    html_content = raw_content
    for company, url in affiliate_links.items():
        if url:
            html_content = html_content.replace(
                f"{{{{{company}}}}}",
                f'<a href="{url}" target="_blank" rel="nofollow sponsored" style="display:inline-block;background:#e8f0fe;color:#1a73e8;padding:4px 12px;border-radius:20px;font-weight:bold;text-decoration:none;">【PR】{company}の公式サイト →</a>'
            )
        else:
            html_content = html_content.replace(f"{{{{{company}}}}}", company)

    result = {
        "keyword": keyword,
        "category": category,
        "html": html_content,
        "generated_at": datetime.now().isoformat(),
        "model": "claude-haiku-4-5-20251001",
        "input_tokens": message.usage.input_tokens,
        "output_tokens": message.usage.output_tokens,
        "cost_estimate_yen": round(
            (message.usage.input_tokens * 0.00000080 + message.usage.output_tokens * 0.000004) * 150, 2
        ),
    }

    return result


def save_article(result: dict) -> Path:
    """生成した記事をHTMLファイルとして保存"""
    slug = re.sub(r"[^\w\s-]", "", result["keyword"]).strip().replace(" ", "-")
    filename = f"{datetime.now().strftime('%Y%m%d')}_{slug}.html"
    filepath = OUTPUT_DIR / filename

    # ページテンプレートに埋め込む
    full_html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{result['keyword']} | マネーコンパス</title>
<link rel="stylesheet" href="../../css/article.css">
<style>
article table {{ width:100%; border-collapse:collapse; margin:24px 0; }}
article table th {{ background:#1B3A6B; color:white; padding:10px 14px; text-align:left; font-size:14px; }}
article table td {{ padding:10px 14px; border-bottom:1px solid #eee; font-size:14px; }}
article table tr:nth-child(even) td {{ background:#f8f9fa; }}
.hero-image {{ border-radius:12px; }}
</style>
</head>
<body>
<header>
  <a href="../../index.html" style="font-size:20px;font-weight:900;color:#1B3A6B;text-decoration:none;">
    マネー<span style="color:#F5A623;">コンパス</span>
  </a>
</header>
<div class="hero-image" style="width:100%;height:280px;overflow:hidden;margin-bottom:32px;">
  <img src="https://images.unsplash.com/photo-1554224155-6726b3ff858f?w=1200&q=80&auto=format&fit=crop"
       alt="カードローン・金融情報"
       style="width:100%;height:100%;object-fit:cover;">
</div>
<div class="layout">
  <main>
    {result['html']}
    <div class="generated-meta" style="font-size:11px;color:#999;margin-top:40px;border-top:1px solid #eee;padding-top:12px;">
      生成日時: {result['generated_at']} | モデル: {result['model']} | 推定コスト: {result['cost_estimate_yen']}円
    </div>
  </main>
</div>
<footer style="background:#1B3A6B;color:rgba(255,255,255,0.6);text-align:center;padding:20px;margin-top:60px;font-size:13px;">
  © 2026 マネーコンパス株式会社 | 本サービスはアフィリエイト広告を含みます
</footer>
</body>
</html>"""

    filepath.write_text(full_html, encoding="utf-8")
    print(f"[WRITE班] 保存完了: {filepath}")

    # WordPressに自動投稿
    wp_result = post_to_wordpress(result["keyword"], result["html"])
    if wp_result["status"] == "success":
        print(f"[WRITE班] WordPress投稿完了: {wp_result['url']}")

    return filepath


def run_daily_batch():
    """今日のキーワードリストを読み込んで一括生成（毎日自動実行）"""
    keywords_file = Path(__file__).parent / "keywords_queue.json"

    if not keywords_file.exists():
        print("[WRITE班] キーワードキューが空です")
        return

    with open(keywords_file, encoding="utf-8") as f:
        queue = json.load(f)

    # todayが空なら upcomingから自動補充
    if not queue.get("today") and queue.get("upcoming"):
        queue["today"] = queue["upcoming"][:5]
        queue["upcoming"] = queue["upcoming"][5:]

    today_keywords = queue.get("today", [])[:5]  # 1日最大5本

    results = []
    for kw in today_keywords:
        try:
            result = generate_article(kw)
            path = save_article(result)
            results.append({"keyword": kw, "file": str(path), "status": "success"})
        except Exception as e:
            results.append({"keyword": kw, "status": "error", "error": str(e)})

    # 処理済みキーワードを移動
    queue["done"] = queue.get("done", []) + today_keywords
    queue["today"] = queue.get("today", [])[5:]

    with open(keywords_file, "w", encoding="utf-8") as f:
        json.dump(queue, f, ensure_ascii=False, indent=2)

    # レポート出力（Slack連携用）
    report = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "generated": len([r for r in results if r["status"] == "success"]),
        "errors": len([r for r in results if r["status"] == "error"]),
        "results": results,
    }

    report_path = Path(__file__).parent / "reports" / f"daily_{datetime.now().strftime('%Y%m%d')}.json"
    report_path.parent.mkdir(exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[WRITE班] 本日の結果: {report['generated']}本成功 / {report['errors']}本失敗")
    return report


# ==========================================
# エントリーポイント
# ==========================================
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "--all":
            run_daily_batch()
        else:
            keyword = " ".join(sys.argv[1:])
            result = generate_article(keyword)
            save_article(result)
            print(f"完了！推定コスト: {result['cost_estimate_yen']}円")
    else:
        print("使い方: python auto_writer.py 'キーワード'")
        print("     または: python auto_writer.py --all")
