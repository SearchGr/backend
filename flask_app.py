import uuid

from flask import Flask, session, jsonify, request, redirect
from flask_cors import CORS

import app_properties
from database import retrieve_user_data, save_user_data
from utils import is_user_authorized, get_instagram_client, \
    exchange_code_for_user_data, start_async_user_media_processing, filter_media_by_search_key

app = Flask(__name__)
CORS(app, supports_credentials=True)


@app.route("/login", methods=["GET"])
def login():
    return redirect(get_instagram_client().get_login_url(), code=302)


@app.route("/callback", methods=["GET"])
def callback():
    code = request.args.get("code")
    user_data = exchange_code_for_user_data(code)

    session_id = uuid.uuid4()
    save_user_data(session_id, user_data)
    session["session_id"] = session_id

    instagram_client = get_instagram_client(user_data.access_token)
    start_async_user_media_processing(instagram_client.get_user_media()['data'])

    return redirect(app_properties.redirect_url, code=302)


@app.route("/checkAuthorization", methods=["GET"])
def check_authorization():
    if is_user_authorized():
        return jsonify({'authorized': True})
    else:
        return jsonify({'authorized': False})


@app.route("/profile/username", methods=["GET"])
def get_profile():
    if is_user_authorized():
        user_data = retrieve_user_data(session['session_id'])
        if user_data is not None:
            instagram_client = get_instagram_client(user_data.access_token)
            username = instagram_client.get_user_profile().get('username')
            return jsonify({'username': username})
    return jsonify()


@app.route("/getPhotos", methods=["GET"])
def get_photos():
    if is_user_authorized():
        user_data = retrieve_user_data(session['session_id'])
        if user_data is not None:
            search_key = request.args.get('key').strip().lower()
            instagram_client = get_instagram_client(user_data.access_token)
            media_list = instagram_client.get_user_media()['data']
            result = filter_media_by_search_key(media_list, search_key)
            if result:
                return jsonify({'media_urls': result})
    return jsonify()


@app.route("/logout", methods=["GET"])
def logout():
    if is_user_authorized():
        session.pop('session_id')
    response = redirect(app_properties.redirect_home, code=302)
    return response


if __name__ == "__main__":
    app.secret_key = app_properties.flask_app_secret
    app.config['SESSION_COOKIE_SAMESITE'] = "None"
    app.config['SESSION_COOKIE_SECURE'] = True
    app.run(debug=True, port=8000)
