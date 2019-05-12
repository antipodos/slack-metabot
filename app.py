from flask import Flask, request, abort, jsonify
from slackbot import create_events_adapter, \
                        post_message_to_my_channels, \
                        who_am_i, \
                        all_my_channels, \
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


@app.route("/whoami", methods=["GET"])
def web_who_am_i():
    return who_am_i().__str__()



@app.route("/mychannels", methods=["GET"])
def web_my_channels():
    return all_my_channels().__str__()


@slack_events_adapter.on("channel_created")
def slack_events_endpoint(data):
    if not request.json:
        abort(400)

    message = "new channel created: {}".format(data["event"]["channel"]["name"])

    redis_queue.enqueue(post_message_to_my_channels, message)

    return jsonify(ok=True)


@app.route("/commands/randomchannel", methods=["POST"])
def slack_command_endpoint_random_channel():
    channel = pick_random_channel()
    return format_channel_info(channel, "There, I picked a random channel for you:")


if __name__ == '__main__':
  app.run()