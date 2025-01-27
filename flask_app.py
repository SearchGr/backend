import uuid
from datetime import timedelta

from flask import Flask, session, jsonify, request, redirect
from flask_cors import CORS

import app_properties
from database import retrieve_user_data, save_user_data
from instagram_utils import get_instagram_client, exchange_code_for_user_data, get_all_user_media
from utils import start_all_user_media_processing, filter_media_by_search_key, start_media_processing_workers, \
    get_processing_progress

app = Flask(__name__)
CORS(app, supports_credentials=True)
NUM_WORKER_THREADS = 3


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
    session.permanent = True

    return redirect(app_properties.SEARCH_PAGE_URL, code=302)


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


@app.route("/profile/update", methods=["GET"])
def update_profile():
    if is_user_authorized():
        user_data = retrieve_user_data(session['session_id'])
        if user_data is not None:
            instagram_client = get_instagram_client(user_data.access_token)
            media = get_all_user_media(instagram_client)
            start_all_user_media_processing(media)

    return jsonify()


@app.route("/profile/progress", methods=["GET"])
def get_progress():
    if is_user_authorized():
        user_data = retrieve_user_data(session['session_id'])
        if user_data is not None:
            instagram_client = get_instagram_client(user_data.access_token)
            progress = get_processing_progress(get_all_user_media(instagram_client))
            return jsonify({'percentage': int(progress * 100)})
    return jsonify()


@app.route("/photos", methods=["GET"])
def get_photos():
    if is_user_authorized():
        user_data = retrieve_user_data(session['session_id'])
        if user_data is not None:
            search_key = request.args.get('key').strip().lower()
            instagram_client = get_instagram_client(user_data.access_token)
            media = get_all_user_media(instagram_client)
            result = filter_media_by_search_key(media, search_key)
            if result:
                return jsonify(result)
    return jsonify([])


@app.route("/logout", methods=["GET"])
def logout():
    if is_user_authorized():
        session.pop('session_id')
    return jsonify()


def is_user_authorized():
    if 'session_id' in session.keys():
        return True
    return False


if __name__ == "__main__":
    start_media_processing_workers(app_properties.NUMBER_OF_MEDIA_PROCESSING_WORKERS)
    app.secret_key = app_properties.FLASK_APP_SECRET
    app.config['SESSION_COOKIE_SAMESITE'] = "None"
    app.config['SESSION_COOKIE_SECURE'] = True
    app.permanent_session_lifetime = timedelta(days=app_properties.SESSION_EXPIRATION_IN_DAYS)
    app.run(debug=True, port=8000)
