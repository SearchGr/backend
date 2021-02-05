from threading import Thread

from PyDictionary import PyDictionary

from database import retrieve, save
from labels import COCO_DATASET_LABELS, IMAGENET_DATASET_LABELS
from media_data import MediaData
from prediction import get_classifications, get_detections
from processing_queue import ProcessingQueue

dictionary = PyDictionary()
media_queue_to_process = ProcessingQueue(maxsize=0)


def start_media_processing_workers(number_of_workers):
    for i in range(number_of_workers):
        Thread(target=handle_user_media_processing, daemon=True).start()


def handle_user_media_processing():
    while True:
        media = media_queue_to_process.get()
        result = retrieve('Media', media[0])
        if result is None:
            process_user_media(media)
        media_queue_to_process.task_done()


def process_user_media(media):
    media_id, media_url = media
    photo_classification = get_classifications(media_url)
    photo_detection = get_detections(media_url)
    media_data = MediaData(photo_classification, photo_detection)
    save('Media', media_id, media_data.__dict__)


def start_all_user_media_processing(media_list):
    for media in media_list:
        if media['media_type'] == 'IMAGE':
            media_queue_to_process.put((media['id'], media['media_url']))


def get_processing_progress(media_list):
    media_tuples = set()
    for media in media_list:
        if media['media_type'] == 'IMAGE':
            media_tuples.add((media['id'], media['media_url']))
    media_count = len(media_tuples)
    return (media_count - len(media_queue_to_process.check_tasks_in_queue(media_tuples))) / media_count


def filter_media_by_search_key(media_list, search_key):
    results = []
    search_keys = {search_key}
    enhance_with_synonyms(search_keys)
    search_keys = to_lowercase_set(search_keys)
    for media in media_list:
        media_data = retrieve('Media', media['id'])
        labels = to_lowercase_set(get_predicted_labels(media_data))
        if search_keys.intersection(labels):
            results.append({'url': media['media_url'], 'permalink': media['permalink']})
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
