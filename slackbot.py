import os
from slack import WebClient
import requests
from slackeventsapi import SlackEventAdapter
import random

token = os.environ["SLACK_API_TOKEN"]
signing_secret = os.environ["SLACK_SIGNING_SECRET"]
metachannel_id = os.environ["SLACK_METACHANNEL_ID"]
footer_message = "<https://metabot.object.farm|a Meta Bot service>"

slack_client = WebClient(token=token)
call_limit = 100


def create_events_adapter(app):
    """
    Creates an event adapter to be used to decorate route methods in flask
    :param app: flask app
    :return: new slack event adapter
    """
    return SlackEventAdapter(signing_secret, "/events", app)


def who_am_i():
    """
    Identity of slack bot
    :return: bot user object (json)
    """

    return slack_client.auth_test()


def all_my_channels():
    """
    Compiles list of all channels the bot is member of
    :return: list of channel objects (json)
    """

    bot_id = who_am_i()["user_id"]

    bot_channels = list()
    for channel in all_channels():
        members = channel_members(channel["id"])
        if bot_id in members:
            bot_channels.append(channel)

    return bot_channels


def inform_about_new_channel(channel_id):
    """
    Informs all channels the bot is member of about a newly created channel
    :param channel_id: id of newly created channel
    """
    channel = slack_client.conversations_info(channel=channel_id)["channel"]
    #post_message_to_my_channels(format_channel_info(channel, "A new channel got created!"))

    #performance fix
    post_message_to_channel(metachannel_id, message=format_channel_info(channel, "A new channel got created!"))


def inform_about_random_channel(channel_to_inform, message):
    """
    Post to channel about a random channel
    :param channel_to_inform: channel to post to
    :param message: pre text message
    """
    post_message_to_channel(channel_to_inform,
                            format_channel_info(
                                pick_random_channel(),
                                message)
                            )


def inform_responseurl_about_random_channel(response_url, message):
    channel = pick_random_channel()
    requests.post(response_url, json=format_channel_info(channel, message))


def inform_responseurl_about_slackstats(response_url, message):
    number_of_channels = len(all_channels())
    requests.post(response_url, json=format_slack_message(message,
                                                          "Slack Stats",
                                                          "Number of Channels: {}".format(number_of_channels),
                                                          footer_message))


def post_message_to_channel(channel_id, message):
    """
    Posts attachments to channel
    :param channel_id: channel to post to
    :param message: attachment essage
    """
    slack_client.chat_postMessage(channel=channel_id, attachments=message["attachments"])


def post_message_to_my_channels(message):
    """
    Post a message in all channels the bot is member of
    :param message: message to post
    """

    for channel in all_my_channels():
        post_message_to_channel(channel_id=channel["id"], message=message)


def all_channels():
    """
    Compiles list of all available public channels
    :return: list of channels
    """

    return paginated_api_call(slack_client.conversations_list,
                                   "channels",
                                   exclude_archived=1,
                                   types="public_channel"
                                   )


def channel_members(channel_id):
    return paginated_api_call(slack_client.conversations_members,
                                   "members",
                                   channel=channel_id,
                                   )


def pick_random_channel():
    """
    Picks a random channel out of all available public channels
    :return: one randomly picked channel
    """

    return random.choice(all_channels())


def paginated_api_call(api_method, response_objects_name, **kwargs):
    """
    Calls api method and cycles through all pages to get all objects
    :param method: api method to call
    :param response_objects_name: name of collection in response json
    :param kwargs: url params to pass to call, additionally to limit and cursor which will be added automatically
    """

    ret = list()
    cursor = None

    while cursor != "":
        if cursor is not None:
            r = api_method(limit=call_limit, cursor=cursor, **kwargs)
        else:
            r = api_method(limit=call_limit, **kwargs)

        response_objects = r.get(response_objects_name)
        if response_objects is not None:
            ret.extend(response_objects)

        metadata = r.get("response_metadata")
        if metadata is not None:
            cursor = metadata["next_cursor"]
        else:
            cursor = ""

    return ret

def format_slack_message(pretext, title, text, footer):
    msg = {
        "attachments": [
            {
                "pretext": pretext,
                "title": title,
                "fallback": title,
                "color": "#2eb886",
                "text": text,
                "mrkdwn_in": [
                    "text",
                    "pretext"
                ],
                "footer": footer
            }
        ]
    }

    return msg


def format_channel_info(channel, pretext):
    purpose = "\n_{}_".format(channel["purpose"]["value"]) if channel["purpose"]["value"] != "" else ""

    return format_slack_message(pretext,
                                "<#{}|{}>".format(channel["id"], channel["name"]),
                                "Created by <@{}>{}".format(channel["creator"], purpose),
                                footer_message)
