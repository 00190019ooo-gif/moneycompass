"""日次レポートをSlackに送信する（GitHub Actionsから呼び出し）"""
import os
import requests

token = os.environ["SLACK_BOT_TOKEN"]
count = os.environ.get("ARTICLE_COUNT", "0")
date = os.environ.get("REPORT_DATE", "")

msg = (
    f"*[WRITE班 日次レポート] {date}*\n"
    f"記事自動生成完了！\n"
    f"累計記事数: {count}本\n"
    f"--- SEC（秘書AI）"
)

requests.post(
    "https://slack.com/api/chat.postMessage",
    headers={"Authorization": f"Bearer {token}"},
    json={"channel": "C0B8QE4ACS1", "text": msg},
)
