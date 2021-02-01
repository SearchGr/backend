import uuid

from flask import Flask, session, jsonify, request, redirect
from flask_cors import CORS
from instagram_basic_display.InstagramBasicDisplay import InstagramBasicDisplay

import app_properties
from database import save, retrieve_user_data, retrieve, save_user_data
from labels import COCO_DATASET_LABELS, IMAGENET_DATASET_LABELS
from media_data import MediaData
from prediction import get_detections, get_classifications
from user_data import UserData

app = Flask(__name__)
CORS(app, supports_credentials=True)

instagram_basic_display = InstagramBasicDisplay(app_id=app_properties.app_id,
                                                app_secret=app_properties.app_secret,
                                                redirect_url=app_properties.callback_url)


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
    if is_user_authorized():
        user_data = retrieve_user_data(session['session_id'])
        if user_data is not None:
            instagram_client = get_instagram_client(user_data.access_token)
            username = instagram_client.get_user_profile().get('username')
            return jsonify({'username': username})
    return jsonify()


@app.route("/getPhotos", methods=["GET"])
def get_photos():
    search_key = request.args.get('key').strip().lower()
    results = set()
    if is_user_authorized():
        user_data = retrieve_user_data(session['session_id'])
        if user_data is not None:
            instagram_client = get_instagram_client(user_data.access_token)
            media_list = instagram_client.get_user_media()
            process_user_media(media_list)
            for data in media_list['data']:
                media_data = retrieve('Media', data['id'])
                if 'detection' in media_data.keys():
                    for detection_id in media_data['detection']:
                        if search_key in split_words(COCO_DATASET_LABELS[detection_id]):
                            results.add(media_data['url'])
                if 'classification' in media_data.keys():
                    for classification_id in media_data['classification']:
                        if search_key in split_words(IMAGENET_DATASET_LABELS[classification_id].lower()):
                            results.add(media_data['url'])
                        # lines = read_data_from_file('imagenet_classes.txt')
                        # words = separate_words_from_line(lines[classification_id])
                        # for word in words:
                        #     if word == search_key:
                        #         results.add(media_data['url'])
    print("before None")
    if results is None:
        results = "There aren't photos with the word you searched!"
        return jsonify(results)
    result = list(results)
    return jsonify({'media_urls': result})


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


def exchange_code_for_user_data(code):
    response = get_instagram_client().get_o_auth_token(code)
    user_id = response.get("user_id")
    # current_time = datetime.now()
    response = get_instagram_client().get_long_lived_token(response.get("access_token"))
    # expires_at = current_time + timedelta(seconds=response.get("expires_in"))
    return UserData(user_id, response.get("access_token"))


def is_user_authorized():
    if 'session_id' in session.keys():
        return True
    return False


def process_user_media(media_list):
    for media in media_list['data']:
        if media['media_type'] == 'IMAGE':
            result = retrieve('Media', media['id'])
            if result is None:
                photo_classification = get_classifications(media['media_url'])
                photo_detection = get_detections(media['media_url'])
                media_data = MediaData(media['media_url'], photo_classification, photo_detection)
                save('Media', media['id'], media_data.__dict__)


def read_data_from_file(file):
    results = []
    file_contain = open(file)
    for line in file_contain:
        results.append(line.rstrip())
    return results


def split_words(line):
    result = line.split(', ')
    return result


if __name__ == "__main__":
    app.secret_key = app_properties.flask_app_secret
    app.config['SESSION_COOKIE_SAMESITE'] = "None"
    app.config['SESSION_COOKIE_SECURE'] = True
    app.run(debug=True, port=8000)
