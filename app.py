import os
import urllib.request
import json
import jwt

from chalice import Chalice, Response
from chalicelib import *

app = Chalice(app_name='chill')


@app.route('/')
def index():
    return {'hello': 'world', 'state': GAME_STATE_NEW}


@app.route('/hello/{name}')
def hello_name(name):
    return {'hello': name}


@app.route('/auth')
def auth():
    auth_code = app.current_request.query_params['code']
    uri = 'https://slack.com/api/oauth.access?client_id=' + os.environ['SLACK_CLIENT_ID'] + '&client_secret='\
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
        redir_url = "http://localhost:4200/?cookie=%s" % encoded_cookie

        return Response(
        status_code=301,
        body='',
        headers={'Location': redir_url})

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