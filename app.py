import os
import urllib.parse
import urllib.request
import json
import jwt
import random

from playhouse.shortcuts import model_to_dict
from slackclient import SlackClient

from chalice import Chalice, Response, BadRequestError
from chalicelib import *

static_site_protocol_host_port = "http://localhost:3000"  # augment with environment var if avail
api_protocol_host_port = "http://localhost:8000"

app = Chalice(app_name='pyfight')
app.debug = True


@app.route('/')
def index():
    return {'hello': 'world', 'state': GAME_STATE_NEW}


@app.route('/favicon.ico')
def favicon():
    return {'hello': 'world', 'state': GAME_STATE_NEW}


@app.route('/{team}/exists', cors=True)
def team_exists(team):
    request_jwt = get_request_jwt()

    try:
        team = Team.get(Team.slack_team_id == request_jwt['team_id'])

        if team.slack_domain is None and team.slack_img is None:
            team.slack_domain = request_jwt['team_domain']
            team.slack_img = request_jwt['team_img']
            team.save()

        return True

    except DoesNotExist:
        return False


@app.route('/{team}/games', cors=True)
def list_team_Games(team):
    request_jwt = get_request_jwt()
    team_from_route = Team.get(Team.slack_domain == team)
    games = Game.get(Game.slack_team == team_from_route)

    clean_games = []
    for game in games:
        clean_games.append(model_to_dict(game, exclude=[Game.slack_team], backrefs=True))

    return clean_games


@app.route('/{team}/game', methods=['POST'], cors=True)
def team_game_by_id(team):
    teamobj = Team.get(Team.slack_domain == team)

    sc = SlackClient(teamobj.slack_bot_access_token)
    channel_list = sc.api_call("channels.list")

    channel_info = sc.api_call("channels.info", channel=channel_list['channels'][0]['id'])  # todo: channel choosing mechanism

    game = Game.create(
        slack_team=teamobj,
        slack_channel_id=channel_info['channel']['id'],
        slack_channel_name=channel_info['channel']['name']
    )
    game.save()

    names = []
    for member_id in channel_info['channel']['members']:
        member = sc.api_call("users.info", user=member_id)
        if not member['user']['is_bot'] and not member['user']['is_app_user']:
            player = Player.create(
                game=game,
                slack_user_id=member['user']['id'],
                name=member['user']['name'],
                img=member['user']['profile']['image_192'],
                x=random.randint(0, game.board_x),
                y=random.randint(0, game.board_y),
            )
            names.append(player.name)
            player.save()

    final_game = Game.get(Game.id == game.id)

    sc.api_call("chat.postMessage", channel=final_game.slack_channel_name,
                text="Call to arms, %s! A game has begun!" % ', '.join(names))

    return model_to_dict(final_game, exclude=[Game.slack_team], backrefs=True)


@app.route('/{team}/game/{gameid}')
def team_game_by_id(team, gameid):
    # agame = Game.get(Game.state == gameid)
    # return agame
    return None


@app.route('/auth')
def auth():
    response = get_slack_auth_response()

    if response['ok']:
        cookie_payload = {
            "user_id": response['user']['id'],
            "user_name": response['user']['name'],
            "user_img": response['user']['image_192'],
            "team_id": response['team']['id'],
            "team_domain": response['team']['domain'],
            "team_img": response['team']['image_230'],
        }

        encoded_cookie = jwt.encode(cookie_payload, os.environ.get('JWT_SECRET'), algorithm='HS256').decode("utf-8")
        return Response(status_code=301, body='',
                        headers={'Location': ("%s/?cookie=%s" % (static_site_protocol_host_port, encoded_cookie))})

    print(json)

    return Response(status_code=301, body='',
                    headers={'Location': ("%s/?err=%s" % (static_site_protocol_host_port, "Login Failed"))})


@app.route('/install')
def slack_install():
    response = get_slack_auth_response(api_protocol_host_port + '/install')

    print(response)

    if response['ok']:

        try:
            team = Team.get(Team.slack_team_id == response['team_id'])
            print("found a team, don't sweat it!")
        except DoesNotExist:
            print("could not find team, creating")
            team = Team.create(
                slack_team_id=response['team_id'],
                slack_access_token=response['access_token'],
                slack_team_name=response['team_name'],
                slack_webhook_url=response['incoming_webhook']['url'],
                slack_bot_id=response['bot']['bot_user_id'],
                slack_bot_access_token=response['bot']['bot_access_token'],
            )
            team.save()
            return Response(status_code=301, body='', headers={'Location': static_site_protocol_host_port})

    return Response(status_code=301, body='',
                    headers={'Location': ("%s/?err=%s" % (static_site_protocol_host_port, "Install Failed"))})


# @app.route('/users', methods=['POST'])
# def create_user():
#     # This is the JSON body the user sent in their POST request.
#     user_as_json = app.current_request.json_body
#     # We'll echo the json body back to the user in a 'user' key.
#     return {'user': user_as_json}
#
# See the README documentation for more examples.
#


def get_slack_auth_response(redirect_uri=None):
    auth_code = app.current_request.query_params['code']
    uri = 'https://slack.com/api/oauth.access?client_id=' \
          + os.environ.get('SLACK_CLIENT_ID') + '&client_secret=' \
          + os.environ.get('SLACK_SECRET') + '&code=' + auth_code

    if redirect_uri is not None:
        url_encode = urllib.parse.quote_plus(redirect_uri)
        uri = uri + '&redirect_uri=' + url_encode

    response = urllib.request.urlopen(uri).read()
    json_response = json.loads(response)
    return json_response


def get_request_jwt():
    try:
        auth_token_value = app.current_request.headers['authorization'].replace('Basic ', '')
        decoded_jwt = jwt.decode(auth_token_value, os.environ.get('JWT_SECRET'), algorithm='HS256')
        return decoded_jwt
    except KeyError:
        raise BadRequestError('Authorization header not provided')
    except jwt.exceptions.DecodeError:
        raise BadRequestError('Authorization header not valid')
