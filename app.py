import os
from flask import Flask, request, make_response, render_template, abort
from slackeventsapi import SlackEventAdapter
import slack

token = os.environ["SLACK_API_TOKEN"]
signing_secret = os.environ["SLACK_SIGNING_SECRET"]

app = Flask(__name__)

slack_client = slack.WebClient(token=token)
slack_events_adapter = SlackEventAdapter(signing_secret, "/events", app)


@app.route("/", methods=["GET"])
def home():
    return "slack meta bot"


@app.route("/whoami", methods=["GET"])
def who_am_i():
    return slack_client.auth_test().__str__()


@app.route("/mychannels", methods=["GET"])
def my_channels():
    return all_my_channels().__str__()


@slack_events_adapter.on("channel_created")
def events(data):
    if not request.json:
        abort(400)
    message = "new channel created: {}".format(data["event"]["channel"]["name"])
    for channel in all_my_channels():
        slack_client.chat_postMessage(channel=channel["id"], text=message)


def all_my_channels():
    bot_id = slack_client.auth_test()["user_id"]

    bot_channels = list()
    for channel in slack_client.conversations_list()["channels"]:
        members = slack_client.conversations_members(channel=channel["id"])["members"]
        if bot_id in members:
            bot_channels.append(channel)

    return bot_channels

if __name__ == '__main__':
  app.run()