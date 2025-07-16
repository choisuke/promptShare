from flask import Flask, render_template, request, redirect, url_for, session
from authlib.integrations.flask_client import OAuth
import os

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

prompts = []

@app.route('/')
def index():
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
        prompts.append({'id': len(prompts), 'content': content, 'likes': 0, 'comments': []})
    return redirect('/')

@app.route('/like/<int:pid>', methods=['POST'])
def like_prompt(pid):
    for p in prompts:
        if p['id'] == pid:
            p['likes'] += 1
            break
    return redirect('/')

@app.route('/comment/<int:pid>', methods=['POST'])
def comment_prompt(pid):
    text = request.form.get('comment')
    user = session.get('user', {}).get('name', 'Anonymous')
    for p in prompts:
        if p['id'] == pid and text:
            p['comments'].append({'user': user, 'text': text})
            break
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
