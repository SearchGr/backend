import json

import pyrebase
from cryptography.fernet import Fernet

import app_properties
from user_data import UserData

firebase_config = {
    "apiKey": "AIzaSyAzlbC3SvhjDm0xF94MrJdFBcQ6YUzXVLE",
    "authDomain": "searchgrdb.firebaseapp.com",
    "databaseURL": "https://searchgrdb-default-rtdb.europe-west1.firebasedatabase.app",
    "projectId": "searchgrdb",
    "storageBucket": "searchgrdb.appspot.com",
    "messagingSenderId": "638305114487",
    "appId": "1:638305114487:web:6952d1520642e25927a972",
    "measurementId": "G-PW56342ECC"
}

firebase = pyrebase.initialize_app(firebase_config)
database = firebase.database()
cipher_suite = Fernet(app_properties.encryption_key)


def get_sessions():
    return database.child('Sessions')


def save(node, key, value):
    database.child(node).child(key).set(value)


def retrieve(node, key):
    result = database.child(node).child(key).get()
    if result.pyres is None:
        return None
    return result.val()


def save_user_data(session_id, user_data):
    encoded_user_data = cipher_suite.encrypt((json.dumps(user_data.__dict__)).encode())
    save('Sessions', session_id, encoded_user_data.decode())


def retrieve_user_data(session_id):
    result = retrieve('Sessions', session_id)
    if result is None:
        return None
    decoded_user_data = json.loads(cipher_suite.decrypt(result.encode()).decode())
    return UserData(decoded_user_data['user_id'], decoded_user_data['access_token'])
