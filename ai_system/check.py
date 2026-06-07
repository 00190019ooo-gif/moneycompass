import anthropic
import schedule
import json
from pathlib import Path

q = json.loads(Path("keywords_queue.json").read_text(encoding="utf-8"))

print("=" * 45)
print(" マネーコンパス AI システムチェック")
print("=" * 45)
print(f" anthropic  : OK (v{anthropic.__version__})")
print(f" schedule   : OK")
print(f" キーワードキュー : 本日{len(q['today'])}件 / 控え{len(q['upcoming'])}件")
print("")
print(" 起動に必要なもの:")
print("   [ ] ANTHROPIC_API_KEY の設定")
print("   [ ] ドメイン取得")
print("   [ ] サーバー契約")
print("")
print(" APIキーを設定した瞬間、記事生成が動き始めます")
print("=" * 45)
