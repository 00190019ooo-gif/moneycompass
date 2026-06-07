import requests

token = 'xoxb-11297788271350-11293567154067-S9V8szu30iS5lkoTM45wxNHA'

CHANNELS = {
    'reports':    'C0B8QE4ACS1',
    'boss':       'C0B8TRL3R7U',
    'all':        'C0B9N47G8E4',
    'logs':       'C0B8QE5QM7F',
}

def post(channel_id: str, text: str):
    r = requests.post(
        'https://slack.com/api/chat.postMessage',
        headers={'Authorization': f'Bearer {token}'},
        json={'channel': channel_id, 'text': text}
    )
    data = r.json()
    if data.get('ok'):
        print(f'[OK] 送信成功: {channel_id}')
    else:
        print(f'[ERR] {channel_id}: {data.get("error")}')
    return data


if __name__ == '__main__':
    report = (
        "*[WRITE班 日次レポート] 2026/06/07*\n"
        "本日の記事生成・WordPress投稿が完了しました！\n\n"
        "*本日投稿済み記事（計５本）*\n"
        "• カードローン おすすめ 比較\n"
        "• カードローン 即日融資 審査\n"
        "• 消費者金融 おすすめ ランキング\n"
        "• カードローン 主婦 審査\n"
        "• カードローン 在籍確認なし おすすめ\n\n"
        "*本日のコスト*: 約13円\n\n"
        "*今後の計画*:\n"
        "- 毎日5本自動生成継続（目標：言30本達成）\n"
        "- 言30本到達次第 Google AdSense申請\n"
        "- afb審査承認後 アコム・プロミス・アイフル等のリンク追加\n"
        "- scheduler.py 常時起動設定（Windowsタスクスケジューラー登録）\n"
        "--- SEC（秘書AI）"
    )
    post(CHANNELS['reports'], report)
    post(CHANNELS['all'], report)