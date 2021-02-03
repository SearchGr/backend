from threading import Thread

from flask import session
from instagram_basic_display.InstagramBasicDisplay import InstagramBasicDisplay

import app_properties
from database import retrieve, save
from media_data import MediaData
from prediction import get_classifications, get_detections
from user_data import UserData

instagram_basic_display = InstagramBasicDisplay(app_id=app_properties.app_id,
                                                app_secret=app_properties.app_secret,
                                                redirect_url=app_properties.callback_url)


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
    for media in media_list:
        if media['media_type'] == 'IMAGE':
            result = retrieve('Media', media['id'])
            if result is None:
                photo_classification = get_classifications(media['media_url'])
                photo_detection = get_detections(media['media_url'])
                media_data = MediaData(media['media_url'], photo_classification, photo_detection)
                save('Media', media['id'], media_data.__dict__)


def start_async_user_media_processing(media_list):
    Thread(target=process_user_media, args=(media_list,), daemon=True).start()
