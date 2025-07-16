from flask import Flask, render_template, request, redirect, url_for, session
from authlib.integrations.flask_client import OAuth
import os
import sqlite3

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET', 'supersecret')

oauth = OAuth(app)

def get_okta_auth():
    okta = oauth.register(
        name='okta',
        client_id=os.environ.get('OKTA_CLIENT_ID'),
        client_secret=os.environ.get('OKTA_CLIENT_SECRET'),
        server_metadata_url=f"{os.environ.get('OKTA_ISSUER')}/.well-known/openid-configuration",
        client_kwargs={
            'scope': 'openid profile email'
        }
    )
    return okta

DB_PATH = os.environ.get('PROMPT_DB', 'prompts.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS prompts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            likes INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prompt_id INTEGER NOT NULL,
            user TEXT,
            text TEXT,
            FOREIGN KEY(prompt_id) REFERENCES prompts(id)
        )
        """
    )
    conn.commit()
    conn.close()

def get_prompts():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, content, likes FROM prompts ORDER BY id DESC")
    prompt_rows = cur.fetchall()
    prompts = []
    for row in prompt_rows:
        cur.execute(
            "SELECT user, text FROM comments WHERE prompt_id=? ORDER BY id ASC",
            (row["id"],),
        )
        comments = [dict(c) for c in cur.fetchall()]
        prompts.append({
            "id": row["id"],
            "content": row["content"],
            "likes": row["likes"],
            "comments": comments,
        })
    conn.close()
    return prompts

@app.route('/')
def index():
    prompts = get_prompts()
    return render_template('index.html', prompts=prompts, user=session.get('user'))

@app.route('/login')
def login():
    okta = get_okta_auth()
    redirect_uri = url_for('auth', _external=True)
    return okta.authorize_redirect(redirect_uri)

@app.route('/auth')
def auth():
    okta = get_okta_auth()
    token = okta.authorize_access_token()
    user = okta.parse_id_token(token)
    session['user'] = {
        'name': user.get('name'),
        'email': user.get('email')
    }
    return redirect('/')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/post', methods=['POST'])
def post_prompt():
    content = request.form.get('content')
    if content:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO prompts (content, likes) VALUES (?, 0)",
            (content,),
        )
        conn.commit()
        conn.close()
    return redirect('/')

@app.route('/like/<int:pid>', methods=['POST'])
def like_prompt(pid):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "UPDATE prompts SET likes = likes + 1 WHERE id = ?",
        (pid,),
    )
    conn.commit()
    conn.close()
    return redirect('/')

@app.route('/comment/<int:pid>', methods=['POST'])
def comment_prompt(pid):
    text = request.form.get('comment')
    user = session.get('user', {}).get('name', 'Anonymous')
    if text:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO comments (prompt_id, user, text) VALUES (?, ?, ?)",
            (pid, user, text),
        )
        conn.commit()
        conn.close()
    return redirect('/')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
