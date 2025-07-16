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
            work_type TEXT NOT NULL,
            summary TEXT,
            expected TEXT,
            user TEXT,
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

def get_prompts_grouped():
    """Return prompts grouped by work_type."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM prompts ORDER BY work_type, id DESC")
    rows = cur.fetchall()
    result = {}
    for row in rows:
        cur.execute(
            "SELECT user, text FROM comments WHERE prompt_id=? ORDER BY id ASC",
            (row["id"],),
        )
        comments = [dict(c) for c in cur.fetchall()]
        prompt = {
            "id": row["id"],
            "content": row["content"],
            "work_type": row["work_type"],
            "summary": row["summary"],
            "expected": row["expected"],
            "user": row["user"],
            "likes": row["likes"],
            "comments": comments,
        }
        result.setdefault(row["work_type"], []).append(prompt)
    conn.close()
    return result

def get_prompt(pid):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM prompts WHERE id=?", (pid,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return None
    cur.execute(
        "SELECT user, text FROM comments WHERE prompt_id=? ORDER BY id ASC",
        (pid,),
    )
    comments = [dict(c) for c in cur.fetchall()]
    conn.close()
    return {
        "id": row["id"],
        "content": row["content"],
        "work_type": row["work_type"],
        "summary": row["summary"],
        "expected": row["expected"],
        "user": row["user"],
        "likes": row["likes"],
        "comments": comments,
    }

@app.route('/')
def index():
    prompts = get_prompts_grouped()
    return render_template('index.html', prompts_by_type=prompts, user=session.get('user'))


@app.route('/prompt/<int:pid>')
def view_prompt(pid):
    prompt = get_prompt(pid)
    if not prompt:
        return redirect('/')
    return render_template('detail.html', prompt=prompt, user=session.get('user'))

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
    work_type = request.form.get('work_type')
    summary = request.form.get('summary')
    expected = request.form.get('expected')
    user = session.get('user', {}).get('name', 'Anonymous')
    if content and work_type:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO prompts (content, work_type, summary, expected, user, likes) VALUES (?, ?, ?, ?, ?, 0)",
            (content, work_type, summary, expected, user),
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
    return redirect(request.referrer or '/')

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
    return redirect(request.referrer or '/')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
