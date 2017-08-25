import os
import urllib.request
import json
import jwt

from chalice import Chalice, Response
from chalicelib import *

static_site_protocol_host_port = "http://localhost:3000"  # augment with environment var if avail

app = Chalice(app_name='chill')


@app.route('/')
def index():
    return {'hello': 'world', 'state': GAME_STATE_NEW}


@app.route('/{team}/exists', cors=True)
def team_exists(team):
    try:
        team = Team.get(Team.slack_domain == team)
        return team is not None
    except DoesNotExist:
        return False


@app.route('/{team}/game/{game_id}')
def team_game_by_id(team, game_id):
    game = Game.get(Game.id == game_id)
    return game


@app.route('/auth')
def auth():
    auth_code = app.current_request.query_params['code']
    uri = 'https://slack.com/api/oauth.access?client_id='\
          + os.environ['SLACK_CLIENT_ID'] + '&client_secret='\
          + os.environ['SLACK_SECRET'] + '&code=' + auth_code
    response = urllib.request.urlopen(uri).read()
    json_response = json.loads(response)

    if json_response['ok']:

        cookie_payload = {
            "user_id": json_response['user']['id'],
            "user_name": json_response['user']['name'],
            "user_img": json_response['user']['image_192'],
            "team_id": json_response['team']['id'],
            "team_domain": json_response['team']['domain'],
            "team_img": json_response['team']['image_230'],
        }

        encoded_cookie = jwt.encode(cookie_payload, os.environ['JWT_SECRET'], algorithm='HS256').decode("utf-8")
        return Response(
            status_code=301,
            body='',
            headers={'Location': ("%s/?cookie=%s" % (static_site_protocol_host_port, encoded_cookie))})

    print(json)

    return {
        "dict": app.current_request.to_dict()
    }

# @app.route('/users', methods=['POST'])
# def create_user():
#     # This is the JSON body the user sent in their POST request.
#     user_as_json = app.current_request.json_body
#     # We'll echo the json body back to the user in a 'user' key.
#     return {'user': user_as_json}
#
# See the README documentation for more examples.
#