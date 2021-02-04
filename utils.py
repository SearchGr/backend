from threading import Thread

from PyDictionary import PyDictionary
from flask import session
from instagram_basic_display.InstagramBasicDisplay import InstagramBasicDisplay

import app_properties
from processing_queue import ProcessingQueue
from database import retrieve, save
from labels import COCO_DATASET_LABELS, IMAGENET_DATASET_LABELS
from media_data import MediaData
from prediction import get_classifications, get_detections
from user_data import UserData

dictionary = PyDictionary()
instagram_basic_display = InstagramBasicDisplay(app_id=app_properties.app_id,
                                                app_secret=app_properties.app_secret,
                                                redirect_url=app_properties.callback_url)
media_queue_to_process = ProcessingQueue(maxsize=0)


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
    response = get_instagram_client().get_long_lived_token(response.get("access_token"))
    return UserData(user_id, response.get("access_token"))


def is_user_authorized():
    if 'session_id' in session.keys():
        return True
    return False


def start_media_processing_workers(number_of_workers):
    for i in range(number_of_workers):
        Thread(target=handle_user_media_processing, daemon=True).start()


def handle_user_media_processing():
    while True:
        media = media_queue_to_process.get()
        print('Processing media with id {}'.format(media[0]))
        process_user_media(media)
        media_queue_to_process.task_done()


def process_user_media(media):
    media_id, media_url = media
    photo_classification = get_classifications(media_url)
    photo_detection = get_detections(media_url)
    media_data = MediaData(media_url, photo_classification, photo_detection)
    save('Media', media_id, media_data.__dict__)


def start_all_user_media_processing(media_list):
    for media in media_list:
        if media['media_type'] == 'IMAGE':
            result = retrieve('Media', media['id'])
            if result is None:
                media_queue_to_process.put((media['id'], media['media_url']))


def filter_media_by_search_key(media_list, search_key):
    results = []
    search_keys = {search_key}
    enhance_with_synonyms(search_keys)
    search_keys = to_lowercase_set(search_keys)
    for data in media_list:
        media_data = retrieve('Media', data['id'])
        labels = to_lowercase_set(get_predicted_labels(media_data))
        if search_keys.intersection(labels):
            results.append(media_data['url'])
    return results


def get_predicted_labels(media_data):
    labels = set()
    if 'detection' in media_data.keys():
        for detection_id in media_data['detection']:
            labels.update(COCO_DATASET_LABELS[detection_id])
    if 'classification' in media_data.keys():
        for classification_id in media_data['classification']:
            labels.update(IMAGENET_DATASET_LABELS[classification_id])
    return labels


def enhance_with_synonyms(words):
    synonyms = set()
    for label in words:
        word_synonyms = dictionary.synonym(label)
        if word_synonyms:
            synonyms.update(word_synonyms)
    words.update(synonyms)


def to_lowercase_set(input_set):
    return set(map(str.lower, input_set))
