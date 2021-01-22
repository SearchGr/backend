# from flask import Flask, make_response, request, render_template, jsonify
# from flask_cors import CORS
#
# app = Flask(__name__)
# CORS(app=app, supports_credentials=True)
#
#
# @app.route("/", methods=["GET"])
# def index():
#     return render_template("index.html")
#
#
# @app.route("/get-cookie/", methods=["GET"])
# def get_cookie():
#     response = make_response("Here, take some cookie!")
#     response.set_cookie(key="id", value="3db4adj3d")
#     return response
#
#
# @app.route("/api/cities/", methods=["GET"])
# def cities():
#     if request.cookies["id"] == "3db4adj3d":
#         cities = [{"name": "Rome", "id": 1}, {"name": "Siena", "id": 2}]
#         return jsonify(cities)
#     return jsonify(msg="Ops!")

from flask import Flask, make_response, request, session, jsonify
from flask_cors import CORS


app = Flask(__name__)
cors = CORS(app, supports_credentials=True)


@app.route("/", methods=["GET"])
def index():
    response = jsonify({"response": "Here, take some cookie!"})
    response.set_cookie(key="cookieName", value="cookieValue")
    session["sessionCookie"] = "sessionCookieValue"
    response.headers.add('Access-Control-Allow-Headers',
                         "Origin, X-Requested-With, Content-Type, Accept, x-auth")
    return response


@app.route("/print", methods=["GET"])
def printing():
    print(request.cookies)
    if "sessionCookie" in session:
        print(session["sessionCookie"])
    return jsonify()


if __name__ == "__main__":
    app.secret_key = "super secret key"
    app.run(debug=True, port=8000)
