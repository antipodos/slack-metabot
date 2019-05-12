from flask import Flask, request, abort, jsonify
import requests
from slackbot import create_events_adapter, \
                        inform_about_new_channel, \
                        inform_about_random_channel, \
                        pick_random_channel, \
                        format_channel_info
from rq import Queue
from worker import conn

app = Flask(__name__)
redis_queue = Queue(connection=conn)
slack_events_adapter = create_events_adapter(app=app)


@app.route("/", methods=["GET"])
def web_home():
    return "slack meta bot"


@slack_events_adapter.on("channel_created")
def slack_events_channel_created(data):
    if not request.json:
        abort(400)
    redis_queue.enqueue(inform_about_new_channel, data["event"]["channel"]["id"])
    return jsonify(ok=True)


@slack_events_adapter.on("app_mention")
def slack_events_app_mention(data):
    message = data["event"]
    channel = message["channel"]

    redis_queue.enqueue(inform_about_random_channel,
                        channel,
                        "I've been summoned? There, I picked a random channel for you:")

    jsonify(ok=True)


@app.route("/commands/randomchannel", methods=["POST"])
def slack_command_endpoint_random_channel():

    try:
        ts = request.headers.get('X-Slack-Request-Timestamp')
        sig = request.headers.get('X-Slack-Signature')
        request.data = request.get_data()
        result = slack_events_adapter.server.verify_signature(ts, sig)
    except:
        result = False

    if not result:
        abort(401)

    response_url = request.form['response_url']

    channel = pick_random_channel()
    requests.post(response_url, json=format_channel_info(channel, "There, I picked a random channel for you:"))


    return jsonify(ok=True)


if __name__ == '__main__':
    app.run()