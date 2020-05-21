"""
    lager.context

    CLI context management
"""
import os
import urllib3
import requests
import click
from requests_toolbelt.sessions import BaseUrlSession
_DEFAULT_HOST = 'https://lagerdata.com'


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
            name = ctx.params['name']
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
    def __init__(self, auth, defaults, style):
        host = os.getenv('LAGER_HOST', _DEFAULT_HOST)
        base_url = '{}{}'.format(host, '/api/v1/')

        self.session = LagerSession(auth, base_url=base_url)
        self.defaults = defaults
        self.style = style

    @property
    def default_gateway(self):
        """
            Get default gateway id from config
        """
        return self.defaults.get('gateway_id')
