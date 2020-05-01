"""
    lager.auth

    Authentication helpers
"""
import os
import base64
import json
import time
import configparser
import datetime
import requests

_DEFAULT_CLIENT_ID = 'Ev4qdcEYIrj4TJLJhJGhhKI9wqWbT7IE'
_DEFAULT_AUDIENCE = 'https://lagerdata.com/api/gateway'
_DEFAULT_AUTH_URL = 'https://lagerdata.auth0.com'

CLIENT_ID = os.getenv('LAGER_CLIENT_ID', _DEFAULT_CLIENT_ID)
AUDIENCE = os.getenv('LAGER_AUDIENCE', _DEFAULT_AUDIENCE)
AUTH_URL = os.getenv('LAGER_AUTH_URL', _DEFAULT_AUTH_URL)

_LAGER_CONFIG_FILE_NAME = '.lager'
_JWK_PATH = '.well-known/jwks.json'

_EXPIRY_GRACE = datetime.timedelta(hours=1).seconds

def _get_config_file_path():
    return os.path.join(os.path.expanduser('~'), _LAGER_CONFIG_FILE_NAME)

def _get_jwks(jwk_url):
    resp = requests.get(jwk_url)
    resp.raise_for_status()
    return resp.json()

def _is_expired(token):
    _header, encoded_payload, _sig = token.split('.')
    payload = json.loads(base64.b64decode(encoded_payload))
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

def read_config_file(config):
    """
        Read our config file into `config` object
    """
    with open(_get_config_file_path()) as f:
        config.read_file(f)

def write_config_file(config):
    """
        Write out `config` into our config file
    """
    with open(_get_config_file_path(), 'w') as f:
        config.write(f)

def load_auth():
    """
        Load auth token from config
    """
    config = configparser.ConfigParser()
    try:
        with open(_get_config_file_path()) as f:
            config.read_file(f)
    except FileNotFoundError:
        return None

    if 'AUTH' not in config or 'token' not in config['AUTH']:
        return None

    if _is_expired(config['AUTH']['token']):
        fresh_token = _refresh(config['AUTH']['refresh'])
        config['AUTH']['token'] = fresh_token['access_token']
        config['AUTH']['type'] = fresh_token['token_type']
        write_config_file(config)

    return config['AUTH']
