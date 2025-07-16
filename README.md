# promptShare

Flaskベースの簡易プロンプト共有サイトです。OktaのOIDCでログインし、プロンプトを投稿したり他のユーザーが投稿したプロンプトに「いいね」やコメントを付けたりできます。投稿内容はSQLiteデータベースに保存されるため、アプリを再起動しても保持されます。

## 必要な環境変数
- `OKTA_CLIENT_ID`
- `OKTA_CLIENT_SECRET`
- `OKTA_ISSUER` (例: `https://dev-xxxx.okta.com/oauth2/default`)
- `FLASK_SECRET` 任意のセッション用シークレット
- `PROMPT_DB` SQLiteのデータベースファイルパス (省略時 `prompts.db`)

## 起動方法
```bash
pip install -r requirements.txt
python app.py
```

初回起動時に `PROMPT_DB` で指定した場所に SQLite データベースが作成されます。

ブラウザで `http://localhost:5000` にアクセスしてください。
