import os
from flask import Flask, request, make_response, render_template, abort
import slack
from flask_sslify import SSLify

token = os.environ["SLACK_API_TOKEN"]
slack_client = slack.WebClient(token=token)

app = Flask(__name__)
SSLify(app)

@app.route("/", methods=["GET"])
def home():
    return "slack meta bot"


@app.route("/event", methods=["POST"])
def events():
    if not request.json:
        abort(400)

    return request.json["challenge"]



if __name__ == '__main__':
  app.run()