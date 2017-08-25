import os
import urllib.parse
import urllib.request
import json
import jwt

from chalice import Chalice, Response
from chalicelib import *

static_site_protocol_host_port = "http://localhost:3000"  # augment with environment var if avail
api_protocol_host_port = "http://localhost:8000"

app = Chalice(app_name='chill')
app.debug = True

@app.route('/')
def index():
    return {'hello': 'world', 'state': GAME_STATE_NEW}


@app.route('/favicon.ico')
def favicon():
    return {'hello': 'world', 'state': GAME_STATE_NEW}


@app.route('/{team}/exists', cors=True)
def team_exists(team):
    try:
        auth = app.current_request.headers['authorization']
        auth = auth.replace('Basic ', '')
        decoded = jwt.decode(auth, os.environ['JWT_SECRET'], algorithm='HS256')
    except KeyError:
        return Response(status_code=401, body='Authorization not provided')
    except jwt.exceptions.DecodeError:
        return Response(status_code=401, body='Authorization not valid')

    try:
        team = Team.get(Team.slack_team_id == decoded['team_id'])

        if team.slack_domain is None and team.slack_img is None:
            team.slack_domain = decoded['team_domain']
            team.slack_img = decoded['team_img']
            team.save()

        return True

    except DoesNotExist:
        return False


@app.route('/{team}/game/{game_id}')
def team_game_by_id(team, game_id):
    game = Game.get(Game.id == game_id)
    return game


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

        encoded_cookie = jwt.encode(cookie_payload, os.environ['JWT_SECRET'], algorithm='HS256').decode("utf-8")
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
          + os.environ['SLACK_CLIENT_ID'] + '&client_secret=' \
          + os.environ['SLACK_SECRET'] + '&code=' + auth_code

    if redirect_uri is not None:
        url_encode = urllib.parse.quote_plus(redirect_uri)
        uri = uri + '&redirect_uri=' + url_encode

    response = urllib.request.urlopen(uri).read()
    json_response = json.loads(response)
    return json_response
