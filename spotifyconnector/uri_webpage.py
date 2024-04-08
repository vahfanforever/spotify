# from flask import Flask, request

# app = Flask(__name__)


# @app.route("/")
# def callback():
#     # code = request.args.get("code")
#     # return code
#     return


# if __name__ == "__main__":
#     app.run()
from flask import Flask, request

app = Flask(__name__)


@app.route("/callback")
def callback():
    access_token = request.args.get("token")
    return f"Access Token: {access_token}"


if __name__ == "__main__":
    app.run(debug=True)
