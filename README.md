# slack-metabot

Slack api bot that provides meta information

## Installation

Best run as heroku app. Deploy to heroku and provision a Redis To Go queue.\
Install to a slack team and provide the following properties as config vars:
- REDISTOGO_URL
- SLACK_API_TOKEN
- SLACK_SIGNING_SECRET

Spin up the web and worker process.

## Functionality

After installation the following functionality is provided

- bot listens to `/randomchannel` slash commands and responds with a randomly picked channel
- bot listens to it being mentioned and - again - responds with a randomly picked channel
- bot listens to the `create_channel` event and posts information about newly created channels into the channels it is member of. 