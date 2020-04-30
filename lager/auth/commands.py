"""
    lager.auth.commands

    auth commands
"""

import os
import time
import configparser
import webbrowser
import requests
import click
from lager.auth import get_config_file_path

_DEFAULT_CLIENT_ID = 'Ev4qdcEYIrj4TJLJhJGhhKI9wqWbT7IE'
_DEFAULT_AUDIENCE = 'https://lagerdata.com/api/gateway'
_DEFAULT_AUTH_URL = 'https://lagerdata.auth0.com'

CLIENT_ID = os.getenv('LAGER_CLIENT_ID', _DEFAULT_CLIENT_ID)
AUDIENCE = os.getenv('LAGER_AUDIENCE', _DEFAULT_AUDIENCE)
AUTH_URL = os.getenv('LAGER_AUTH_URL', _DEFAULT_AUTH_URL)

SCOPE = 'read:gateway flash:duck offline_access'

def poll_for_token(device_code, interval):
    """
        Poll for an auth token for the specified device at the given interval
    """
    data = {
        'grant_type': 'urn:ietf:params:oauth:grant-type:device_code',
        'device_code': device_code,
        'client_id': CLIENT_ID,
    }
    token_url = '{}/oauth/token'.format(AUTH_URL)
    while True:
        resp = requests.post(token_url, data=data)
        if resp.status_code == 200:
            return resp.json()

        if resp.status_code >= 500:
            resp.raise_for_status()

        error = resp.json()['error']
        if error == 'authorization_pending':
            time.sleep(interval)
        elif error == 'expired_token':
            click.secho('Session timed out. Please run `lager login` again.', err=True, fg='red')
            click.get_current_context().exit(1)
        elif error == 'access_denied':
            click.secho('Access denied.', err=True, fg='red')
            click.get_current_context().exit(1)


@click.command()
def login():
    """
        Log in
    """
    has_browser = True
    try:
        webbrowser.get()
    except webbrowser.Error:
        has_browser = False

    data = {
        'audience': AUDIENCE,
        'scope': SCOPE,
        'client_id': CLIENT_ID,
    }
    code_url = '{}/oauth/device/code'.format(AUTH_URL)
    response = requests.post(code_url, data=data)
    response.raise_for_status()

    code_response = response.json()
    uri = code_response['verification_uri_complete']
    user_code = code_response['user_code']
    if has_browser:
        click.echo('Please confirm the following code appears in your browser: ', nl=False)
        click.secho(user_code, fg='green')
        if click.confirm('Lager would like to open a browser window to confirm your login info'):
            webbrowser.open_new(uri)
        else:
            click.echo('Cancelled')
    else:
        click.echo('Please visit ', nl=False)
        click.secho(uri, fg='green', nl=False)
        click.echo(' in your browser')
        click.echo('And confirm your device token: ', nl=False)
        click.secho(user_code, fg='green')

    click.echo('Awaiting login...')
    payload = poll_for_token(code_response['device_code'], code_response['interval'])
    click.secho('Success! You\'re ready to use Lager!', fg='green')

    config = configparser.ConfigParser()
    config['AUTH'] = {
        'Token': payload['access_token'],
        'Type': payload['token_type'],
        'Refresh': payload['refresh_token'],
    }
    with open(get_config_file_path(), 'w') as f:
        config.write(f)

@click.command()
def logout():
    """
        Log out
    """
    config = configparser.ConfigParser()
    try:
        with open(get_config_file_path()) as f:
            config.read_file(f)
    except FileNotFoundError:
        return

    if 'AUTH' in config:
        del config['AUTH']

    with open(get_config_file_path(), 'w') as f:
        config.write(f)
