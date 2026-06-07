# Make.com フロー設定ガイド
**担当: TECH班 | Make.com登録後にこの手順でフローを作る**

---

## フロー1：Slack → AIチーム → Slack（Boss指示受け）

Make.com登録後、以下の順で設定する。

### ステップ1: 新しいシナリオを作成
1. Make.com にログイン
2. 「Create a new scenario」をクリック
3. 名前：「SEC - Boss指示受付」

### ステップ2: トリガーを設定
1. 「+」をクリック → 「Slack」を選択
2. アクション：「Watch Messages」
3. チャンネル：「boss-commands」
4. SlackのAPIトークンを入力（Slackの設定→APIから取得）

### ステップ3: Claude APIで内容を解析
1. 「+」→「HTTP」→「Make a request」
2. URL：`https://api.anthropic.com/v1/messages`
3. Method：POST
4. Headers：
   ```
   anthropic-version: 2023-06-01
   x-api-key: [ClaudeのAPIキー]
   content-type: application/json
   ```
5. Body（JSON）：
   ```json
   {
     "model": "claude-haiku-4-5-20251001",
     "max_tokens": 500,
     "system": "あなたはSECです。Bossの指示を受けて、どの班に振るか判断し、タスクを日本語で簡潔に返してください。",
     "messages": [{"role": "user", "content": "{{1.text}}"}]
   }
   ```

### ステップ4: 結果をSlackに返す
1. 「+」→「Slack」→「Create a Message」
2. チャンネル：「reports」
3. テキスト：`SEC完了: {{3.content[0].text}}`

---

## フロー2：毎日09:00 記事自動生成

### トリガー
- Schedule → Every day at 09:00

### アクション
- HTTP POST → サーバーの `auto_writer.py` を実行
  （サーバー設定後にWebhook URLを設定）

---

## フロー3：毎月1日 収益レポートをSlackに送る

### トリガー
- Schedule → Every month on day 1

### アクション1: Stripe APIから売上取得
- HTTP GET → `https://api.stripe.com/v1/balance_transactions`
- Headers: `Authorization: Bearer [StripeのAPIキー]`

### アクション2: Claudeでレポート文章を生成
- HTTP POST → Claude API

### アクション3: Slackに送信
- チャンネル：`reports`
- 月次レポートをBossに自動投稿

---

## Make.com登録直後にやること

1. Slackアプリを追加（App Directory → Slack）
2. APIトークン入力
3. フロー1をまず作ってテスト送信してみる

*フローが動いたら、以後は触らなくていい*
