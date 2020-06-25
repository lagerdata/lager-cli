"""
    lager.auth

    Authentication helpers
"""
import os
import base64
import json
import time
import datetime
import requests
from ..config import read_config_file, write_config_file

_DEFAULT_CLIENT_ID = 'Ev4qdcEYIrj4TJLJhJGhhKI9wqWbT7IE'
_DEFAULT_AUDIENCE = 'https://lagerdata.com/gateway'
_DEFAULT_AUTH_URL = 'https://lagerdata.auth0.com/'

CLIENT_ID = os.getenv('LAGER_CLIENT_ID', _DEFAULT_CLIENT_ID)
AUDIENCE = os.getenv('LAGER_AUDIENCE', _DEFAULT_AUDIENCE)
AUTH_URL = os.getenv('LAGER_AUTH_URL', _DEFAULT_AUTH_URL)

_JWK_PATH = '.well-known/jwks.json'

_EXPIRY_GRACE = datetime.timedelta(hours=1).seconds

def _get_jwks(jwk_url):
    resp = requests.get(jwk_url)
    resp.raise_for_status()
    return resp.json()

def _is_expired(token):
    _header, encoded_payload, _sig = token.split('.')
    padding = '===='  # Auth0 token does not include padding
    payload = json.loads(base64.b64decode(encoded_payload + padding))
    return payload['exp'] < time.time() + _EXPIRY_GRACE

def _refresh(refresh_token):
    data = {
        'grant_type': 'refresh_token',
        'client_id': CLIENT_ID,
        'refresh_token': refresh_token,
    }
    token_url = '{}oauth/token'.format(AUTH_URL)
    resp = requests.post(token_url, data=data)
    resp.raise_for_status()
    return resp.json()

AUTH_TOKEN_KEY = 'LAGER_AUTH_TOKEN'
REFRESH_TOKEN_KEY = 'LAGER_REFRESH_TOKEN'
TOKEN_TYPE_KEY = 'LAGER_TOKEN_TYPE'
def _load_auth_from_environ(env):
    if AUTH_TOKEN_KEY in env and REFRESH_TOKEN_KEY in env and TOKEN_TYPE_KEY in env:
        return dict(
            token=env[AUTH_TOKEN_KEY],
            refresh=env[REFRESH_TOKEN_KEY],
            type=env[TOKEN_TYPE_KEY],
        )
    return None

def load_auth():
    """
        Load auth token from environment if available, otherwise config
    """
    auth = None
    update_config = False
    auth = _load_auth_from_environ(os.environ)
    if not auth:
        config = read_config_file()
        if 'AUTH' not in config or 'token' not in config['AUTH']:
            return None
        update_config = True
        auth = config['AUTH']

    if _is_expired(auth['token']):
        fresh_token = _refresh(auth['refresh'])
        auth['token'] = fresh_token['access_token']
        auth['type'] = fresh_token['token_type']
        if update_config:
            write_config_file(config)

    return auth
