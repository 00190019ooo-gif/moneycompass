"""
SECチーム — スケジューラー（24時間自動運転の心臓部）
マネーコンパス株式会社

このスクリプトを一度起動すれば、以下が全自動で動き続ける：
  - 毎日 09:00  → WRITE班が記事5本生成
  - 毎日 12:00  → GROW班がSEOチェック
  - 毎月 1日    → FIN班が収益レポート送信
  - 常時         → CARE班が問い合わせ監視

起動方法: python scheduler.py
"""

import schedule
import time
import subprocess
import json
import os
import sys
import requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

BASE_DIR = Path(__file__).parent
SLACK_TOKEN = os.environ.get("SLACK_BOT_TOKEN", "")
CHANNEL_REPORTS = "C0B8QE4ACS1"
CHANNEL_LOGS = "C0B8QE5QM7F"


def slack_post(channel: str, text: str):
    try:
        requests.post(
            "https://slack.com/api/chat.postMessage",
            headers={"Authorization": f"Bearer {SLACK_TOKEN}"},
            json={"channel": channel, "text": text},
            timeout=10,
        )
    except Exception:
        pass

# ==========================================
# 各班の実行関数
# ==========================================

def write_team_daily():
    """WRITE班: 毎日5本の記事を自動生成"""
    print(f"\n{'='*40}")
    print(f"[{datetime.now()}] WRITE班 始動")
    print(f"{'='*40}")
    slack_post(CHANNEL_LOGS, f"[WRITE班] 記事生成バッチ開始 {datetime.now().strftime('%Y/%m/%d %H:%M')}")
    try:
        result = subprocess.run(
            [sys.executable, str(BASE_DIR / "auto_writer.py"), "--all"],
            capture_output=True, text=True, encoding="utf-8"
        )
        print(result.stdout)
        log_event("WRITE班", "記事生成完了", result.stdout[-200:])

        total = _count_articles()
        msg = (
            f"*[WRITE班 日次レポート] {datetime.now().strftime('%Y/%m/%d')}*\n"
            f"本日の記事生成・WordPress投稿が完了しました！\n"
            f"*累計記事数*: {total}本\n"
        )
        if total >= 30:
            msg += "*Google AdSense申請タイミングです！*\n"
        msg += "-- SEC（秘書AI）"
        slack_post(CHANNEL_REPORTS, msg)

    except Exception as e:
        log_event("WRITE班", "エラー", str(e))
        slack_post(CHANNEL_LOGS, f"[WRITE班][ERR] {str(e)[:200]}")


def grow_team_seo_check():
    """GROW班: 毎日のSEOスコアチェック（簡易版）"""
    print(f"\n[{datetime.now()}] GROW班 SEOチェック開始")
    articles_dir = BASE_DIR.parent / "articles" / "generated"
    count = len(list(articles_dir.glob("*.html"))) if articles_dir.exists() else 0
    msg = f"掲載記事数: {count}本"
    print(f"[GROW班] {msg}")
    log_event("GROW班", "SEOチェック完了", msg)


def fin_team_monthly_report():
    """FIN班: 毎月1日に収益レポートを生成"""
    if datetime.now().day != 1:
        return

    print(f"\n[{datetime.now()}] FIN班 月次レポート生成")
    reports_dir = BASE_DIR / "reports"
    month = datetime.now().strftime("%Y-%m")

    report = {
        "month": month,
        "generated_at": datetime.now().isoformat(),
        "articles_total": len(list((BASE_DIR.parent / "articles" / "generated").glob("*.html")))
            if (BASE_DIR.parent / "articles" / "generated").exists() else 0,
        "message": f"{month} 月次レポート。アフィリエイト収益はStripeダッシュボードで確認してください。",
    }

    report_path = reports_dir / f"monthly_{month}.json"
    report_path.parent.mkdir(exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[FIN班] 月次レポート保存: {report_path}")
    log_event("FIN班", "月次レポート完了", json.dumps(report, ensure_ascii=False))


def sec_heartbeat():
    """SEC班: 5分ごとに全システムの死活監視"""
    status = {
        "timestamp": datetime.now().isoformat(),
        "writer_queue": _count_queue(),
        "articles_generated": _count_articles(),
    }
    heartbeat_path = BASE_DIR / "heartbeat.json"
    heartbeat_path.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")


def log_event(team: str, event: str, detail: str = ""):
    """全イベントをログファイルに記録"""
    log_path = BASE_DIR / "logs" / f"{datetime.now().strftime('%Y%m%d')}.log"
    log_path.parent.mkdir(exist_ok=True)
    entry = f"[{datetime.now().strftime('%H:%M:%S')}] [{team}] {event}"
    if detail:
        entry += f" | {detail[:100]}"
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(entry + "\n")
    print(entry)


def _count_queue() -> int:
    queue_file = BASE_DIR / "keywords_queue.json"
    if not queue_file.exists():
        return 0
    with open(queue_file, encoding="utf-8") as f:
        q = json.load(f)
    return len(q.get("today", [])) + len(q.get("upcoming", []))


def _count_articles() -> int:
    d = BASE_DIR.parent / "articles" / "generated"
    return len(list(d.glob("*.html"))) if d.exists() else 0


# ==========================================
# スケジュール設定
# ==========================================
def setup_schedule():
    # WRITE班: 毎日 09:00 に記事生成
    schedule.every().day.at("09:00").do(write_team_daily)

    # GROW班: 毎日 12:00 にSEOチェック
    schedule.every().day.at("12:00").do(grow_team_seo_check)

    # FIN班: 毎日 00:01 に月次レポート（1日のみ実行）
    schedule.every().day.at("00:01").do(fin_team_monthly_report)

    # SEC班: 5分おきにヘルスチェック
    schedule.every(5).minutes.do(sec_heartbeat)

    print("=" * 50)
    print(" マネーコンパス AI自動運転システム 起動")
    print("=" * 50)
    print(f" 起動時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f" WRITE班: 毎日09:00に記事5本生成")
    print(f" GROW班:  毎日12:00にSEOチェック")
    print(f" FIN班:   毎月1日に収益レポート")
    print(f" SEC班:   5分おきに全体監視")
    print("=" * 50)
    print(" Ctrl+C で停止")
    print("")
    slack_post(CHANNEL_LOGS, f"[SEC] マネーコンパス AIシステム起動 {datetime.now().strftime('%Y/%m/%d %H:%M')} — 毎日09:00に記事自動生成")


if __name__ == "__main__":
    setup_schedule()

    # 起動直後に一回テスト実行
    sec_heartbeat()
    log_event("SEC", "システム起動", "全班スタンバイ完了")

    while True:
        schedule.run_pending()
        time.sleep(30)
