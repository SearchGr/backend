import io
import uuid
import os
import sys

import requests
import torch
import torchvision
from PIL import Image
from flask import Flask, session, jsonify, request, redirect
from flask_cors import CORS
from instagram_basic_display.InstagramBasicDisplay import InstagramBasicDisplay
from torchvision import models
from torchvision import transforms

import app_properties
import detect_utils
from database import save, retrieve_user_data, retrieve
from media_data import MediaData
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
    save('Sessions', session_id, user_data.__dict__)
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
    search_key = request.args.get('key')
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
                        if detect_utils.coco_names[detection_id] == search_key:
                            results.add(media_data['url'])
                if 'classification' in media_data.keys():
                    for classification_id in media_data['classification']:
                        lines = read_data_from_file('imagenet_classes.txt')
                        words = separate_words_from_line(lines[classification_id])
                        for word in words:
                            if word == search_key:
                                results.add(media_data['url'])
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
                photo_classification = classify(media['media_url'])
                photo_detection = detection(media['media_url'])
                media_data = MediaData(media['media_url'], photo_classification, photo_detection)
                save('Media', media['id'], media_data.__dict__)


def detection(url):
    response = requests.get(url)
    image_bytes = io.BytesIO(response.content)

    model = torchvision.models.detection.fasterrcnn_resnet50_fpn(pretrained=True,
                                                                 min_size=800)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    image = Image.open(image_bytes)
    model.eval().to(device)
    boxes, classes, labels = detect_utils.predict(image, model, device, app_properties.detection_threshold)
    result_set = set()
    for label in labels:
        result_set.add(label.item())
    result = list(result_set)
    return result


def classify(url):
    resnet = models.resnet101(pretrained=True)
    response = requests.get(url)
    image_bytes = io.BytesIO(response.content)

    img = Image.open(image_bytes)

    preprocess = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        )])

    img_preprocessed = preprocess(img)

    batch_img_cat_tensor = torch.unsqueeze(img_preprocessed, 0)

    resnet.eval()

    out = resnet(batch_img_cat_tensor)

    with open('imagenet_classes.txt') as f:
        labels = [line.strip() for line in f.readlines()]

    _, index = torch.max(out, 1)

    percentage = torch.nn.functional.softmax(out, dim=1)[0] * 100

    # print(labels[index[0]], percentage[index[0]].item())

    _, indices = torch.sort(out, descending=True)
    i = 0
    result = []
    while indices[0][i]:
        if percentage[indices[0][i]].item() > app_properties.classification_threshold * 100:
            result.append(indices[0][i].item())
        i += 1
    return result


def read_data_from_file(file):
    results = []
    file_contain = open(file)
    for line in file_contain:
        results.append(line.rstrip())
    return results


def separate_words_from_line(line):
    result = line.split(', ')
    return result


if __name__ == "__main__":
    app.secret_key = "super secret key"
    app.config['SESSION_COOKIE_SAMESITE'] = "None"
    app.config['SESSION_COOKIE_SECURE'] = True
    app.run(debug=True, port=8000)
    # print(read_data_from_file('imagenet_classes.txt'))
