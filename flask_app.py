import uuid
from datetime import datetime, timedelta

from flask import Flask, session, jsonify, request, redirect
from flask_cors import CORS
from instagram_basic_display.InstagramBasicDisplay import InstagramBasicDisplay

import app_properties
from user_authorization import UserAuthorization

app = Flask(__name__)
CORS(app, supports_credentials=True)

db = {}
instagram_basic_display = InstagramBasicDisplay(app_id=app_properties.app_id,
                                                app_secret=app_properties.app_secret,
                                                redirect_url=app_properties.callback_url)


@app.route("/login", methods=["GET"])
def login():
    return redirect(get_instagram_client().get_login_url(), code=302)


@app.route("/callback", methods=["GET"])
def callback():
    code = request.args.get("code")
    user_authorization = retrieve_user_authorization(code)

    session_id = uuid.uuid4()
    save_session(session_id, user_authorization)
    session["session_id"] = session_id

    response = redirect(app_properties.redirect_url, code=302)
    return response


@app.route("/checkAuthorization", methods=["GET"])
def check_authorization():
    if is_user_authorized():
        return jsonify({'authorized': True})
    else:
        return jsonify({'authorized': False})


@app.route("/profile/username", methods=["GET"])
def get_profile():
    # session["session_id"] = "ilinca"
    if is_user_authorized():
        instagram_client = get_instagram_client(get_user_authorization(session['session_id']).access_token)
        # instagram_client = get_instagram_client(get_user_authorization(session['session_id']).get("access_token"))
        username = instagram_client.get_user_profile().get('username')
        print(username)
        return jsonify({'username': username})
    return jsonify()


@app.route("/getPhotos", methods=["GET"])
def get_photos():
    search_key = request.args.get('key')
    print(search_key)
    if is_user_authorized():
        instagram_client = get_instagram_client(get_user_authorization(session['session_id']).access_token)
        media = instagram_client.get_user_media()
        media_url = []
        for i in media['data']:
            if i['media_type'] == 'IMAGE':
                media_url.append(i['media_url'])
    return jsonify({'media_url': media_url})


@app.route("/logout", methods=["GET"])
def logout():
    if is_user_authorized():
        session.pop('session_id')
    response = redirect(app_properties.redirect_home, code=302)
    return response


def get_instagram_client(access_token=None):
    if access_token:
        instagram_client = InstagramBasicDisplay(app_id=app_properties.app_id,
                                                 app_secret=app_properties.app_secret,
                                                 redirect_url=app_properties.callback_url)
        instagram_client.set_access_token(access_token)
        return instagram_client
    return instagram_basic_display


def retrieve_user_authorization(code):
    response = get_instagram_client().get_o_auth_token(code)
    user_id = response.get("user_id")
    current_time = datetime.now()
    response = get_instagram_client().get_long_lived_token(response.get("access_token"))
    expires_at = current_time + timedelta(seconds=response.get("expires_in"))
    return UserAuthorization(user_id, response.get("access_token"), expires_at)


def is_user_authorized():
    if 'session_id' in session.keys():
        return True
    return False


def save_session(session_id, user_authorization):
    db[session_id] = user_authorization


def get_user_authorization(session_id):
    return db[session_id]


if __name__ == "__main__":
    app.secret_key = "super secret key"
    app.config['SESSION_COOKIE_SAMESITE'] = "None"
    app.config['SESSION_COOKIE_SECURE'] = True
    # save_session("ilinca", {
    #     "access_token": "IGQVJWQmVZARVJDUEhvWGhjZA2tBYVlReDJmZAkNyaGxTN29IWHpzdk82Mm40QWtwT2JYUFJJVU1LanVNOF9qeWNXaF8zMzdtRWZAiY0tjanFfcU5MUjJVYXRTVDYxTUlhT1c5QzRQSDVB"})
    app.run(debug=True, port=8000)
