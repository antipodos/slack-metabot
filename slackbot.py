import os
from slack import WebClient
from slackeventsapi import SlackEventAdapter
import random

token = os.environ["SLACK_API_TOKEN"]
signing_secret = os.environ["SLACK_SIGNING_SECRET"]
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


def post_message_to_my_channels(message):
    """
    Post a message in all channels the bot is member of
    :param message: message to post
    """

    for channel in all_my_channels():
        slack_client.chat_postMessage(channel=channel["id"], text=message)


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
