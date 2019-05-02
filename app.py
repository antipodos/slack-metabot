import os
from flask import Flask, request, make_response, render_template, abort
from flask_talisman import Talisman
import slack

token = os.environ["SLACK_API_TOKEN"]
slack_client = slack.WebClient(token=token)

app = Flask(__name__)
Talisman(app, force_https=True)

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