"""
    lager.context

    CLI context management
"""
import os
import urllib.parse
import urllib3
import requests
import click
from requests_toolbelt.sessions import BaseUrlSession

_DEFAULT_HOST = 'https://lagerdata.com'
_DEFAULT_WEBSOCKET_HOST = 'wss://ws.lagerdata.com'

class LagerSession(BaseUrlSession):
    """
        requests session wrapper
    """

    @staticmethod
    def handle_errors(r, *args, **kwargs):
        """
            Handle request errors
        """
        ctx = click.get_current_context()
        if r.status_code == 404:
            name = ctx.params['name'] or ctx.obj.default_gateway
            click.secho('You don\'t have a gateway with id `{}`'.format(name), fg='red', err=True)
            click.secho(
                'Please double check your login credentials and gateway id',
                fg='red',
                err=True,
            )
            ctx.exit(1)
        if r.status_code == 422:
            error = r.json()['error']
            click.secho(error['description'], fg='red', err=True)
            ctx.exit(1)
        if r.status_code >= 500:
            click.secho('Something went wrong with the Lager API', fg='red', err=True)
            ctx.exit(1)

        r.raise_for_status()

    def __init__(self, auth, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._connection_exception = None
        verify = 'NOVERIFY' not in os.environ
        if not verify:
            urllib3.disable_warnings()

        auth_header = {
            'Authorization': '{} {}'.format(auth['type'], auth['token'])
        }
        self.headers.update(auth_header)
        self.verify = verify
        self.hooks['response'].append(LagerSession.handle_errors)


    def request(self, *args, **kwargs):
        """
            Catch connection errors so they can be handled more cleanly
        """
        try:
            return super().request(*args, **kwargs)
        except requests.exceptions.ConnectTimeout:
            click.secho('Connection to Lager API timed out', fg='red', err=True)
            click.get_current_context().exit(1)
        except requests.exceptions.ConnectionError:
            click.secho('Could not connect to Lager API', fg='red', err=True)
            click.get_current_context().exit(1)


class LagerContext:  # pylint: disable=too-few-public-methods
    """
        Lager Context manager
    """
    def __init__(self, auth, defaults, debug, style):
        host = os.getenv('LAGER_HOST', _DEFAULT_HOST)
        ws_host = os.getenv('LAGER_WS_HOST', _DEFAULT_WEBSOCKET_HOST)
        base_url = '{}{}'.format(host, '/api/v1/')

        self.session = LagerSession(auth, base_url=base_url)
        self.defaults = defaults
        self.style = style
        self.ws_host = ws_host
        self.debug = debug
        self.auth_token = auth['token']

    @property
    def default_gateway(self):
        """
            Get default gateway id from config
        """
        return self.defaults.get('gateway_id')

    def websocket_connection_params(self, socktype, **kwargs):
        """
            Yields a websocket connection to the given path
        """
        if socktype == 'job':
            path = f'/job/{kwargs["job_id"]}'
        elif socktype == 'gdb-tunnel':
            path = f'/gateway/{kwargs["gateway_id"]}/gdb-tunnel'
        else:
            raise ValueError(f'Invalid websocket type: {socktype}')
        uri = urllib.parse.urljoin(self.ws_host, path)

        headers = [
            (b'authorization', self.session.headers['Authorization'].encode()),
        ]

        return (uri, dict(extra_headers=headers))
