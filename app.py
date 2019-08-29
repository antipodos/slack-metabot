from flask import Flask, request, abort, jsonify, render_template
from flask_bootstrap import Bootstrap
from slackbot import create_events_adapter, \
                        inform_about_new_channel, \
                        inform_about_random_channel, \
                        inform_responseurl_about_random_channel

from rq import Queue
from worker import conn

app = Flask(__name__)
Bootstrap(app)
redis_queue = Queue(connection=conn)
slack_events_adapter = create_events_adapter(app=app)

redis_reported_channels_key = "reported_channels"


@app.route("/", methods=["GET"])
def web_home():
    return render_template("main.html")


@slack_events_adapter.on("channel_created")
def slack_events_channel_created(data):
    if not request.json:
        abort(400)

    channel_id = data["event"]["channel"]["id"]

    if not channel_got_reported(channel_id):
        redis_queue.enqueue(inform_about_new_channel, channel_id)
        add_channel_to_reported_channels(channel_id)

    return jsonify(ok=True)


def add_channel_to_reported_channels(channel_id):
    conn.sadd(redis_reported_channels_key, channel_id)


def channel_got_reported(channel_id):
    return conn.sismember(redis_reported_channels_key, channel_id)


@slack_events_adapter.on("app_mention")
def slack_events_app_mention(data):
    message = data["event"]
    channel = message["channel"]

    redis_queue.enqueue(inform_about_random_channel,
                        channel,
                        "I've been summoned? There, I picked a random channel for you:")

    return jsonify(ok=True)


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

    redis_queue.enqueue(inform_responseurl_about_random_channel,
                        request.form['response_url'],
                        "There, I picked a random channel for you:")

    return '', 200


if __name__ == '__main__':
    app.run()