# promptShare

Flaskベースの簡易プロンプト共有サイトです。OktaのOIDCでログインし、プロンプトを投稿したり他のユーザーが投稿したプロンプトに「いいね」やコメントを付けたりできます。データはメモリ上に保持しているため、アプリを再起動すると消えます。

## 必要な環境変数
- `OKTA_CLIENT_ID`
- `OKTA_CLIENT_SECRET`
- `OKTA_ISSUER` (例: `https://dev-xxxx.okta.com/oauth2/default`)
- `FLASK_SECRET` 任意のセッション用シークレット

## 起動方法
```bash
pip install -r requirements.txt
python app.py
```

ブラウザで `http://localhost:5000` にアクセスしてください。
