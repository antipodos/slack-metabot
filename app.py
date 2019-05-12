from flask import Flask, request, abort, jsonify
from slackbot import SlackBot
from rq import Queue
from worker import conn

app = Flask(__name__)
bot = SlackBot()
redis_queue = Queue(connection=conn)

slack_events_adapter = bot.create_events_adapter(app=app)


@app.route("/", methods=["GET"])
def web_home():
    return "slack meta bot"


@app.route("/whoami", methods=["GET"])
def web_who_am_i():
    return bot.who_am_i().__str__()


@app.route("/mychannels", methods=["GET"])
def web_my_channels():
    return bot.all_my_channels().__str__()


@slack_events_adapter.on("channel_created")
def slack_events_endpoint(data):
    if not request.json:
        abort(400)

    message = "new channel created: {}".format(data["event"]["channel"]["name"])

    redis_queue.enqueue(bot.post_message_to_my_channels, message)

    return jsonify(ok=True)


@app.route("/commands/randomchannel", methods=["POST"])
def slack_command_endpoint_random_channel():
    channel = bot.pick_random_channel()
    return "I picked '{}' for you".format(channel["name"])


if __name__ == '__main__':
  app.run()