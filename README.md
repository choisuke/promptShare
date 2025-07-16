# promptShare

Flaskベースの簡易プロンプト共有サイトです。OktaのOIDCでログインし、プロンプトを投稿したり他のユーザーが投稿したプロンプトに「いいね」やコメントを付けたりできます。投稿内容はSQLiteデータベースに保存されるため、アプリを再起動しても保持されます。

投稿時には以下を入力します。

- プロンプト本文
- 業務のタイプ（選択式）
- 業務の概要
- 得られる結果の説明

投稿されたプロンプトは業務タイプごとに一覧表示され、各プロンプトの詳細ページでは概要や期待される結果、投稿者名、コメント一覧を確認できます。

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
