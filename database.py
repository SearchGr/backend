import pyrebase

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


def get_sessions():
    return database.child('Sessions')


def save(node, key, value):
    database.child(node).child(key).set(value)


def retrieve(node, key):
    result = database.child(node).child(key).get()
    if result.pyres is None:
        return None
    return result.val()


def retrieve_user_data(session_id):
    result = retrieve('Sessions', session_id)
    if result is None:
        return None
    return UserData(result['user_id'], result['access_token'])
