from instagram_basic_display.InstagramBasicDisplay import InstagramBasicDisplay

import app_properties
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
    response = get_instagram_client().get_long_lived_token(response.get("access_token"))
    return UserData(user_id, response.get("access_token"))
