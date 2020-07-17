"""
    lager.context

    CLI context management
"""
import os
import json
import ssl
import urllib.parse
import urllib3
import requests
import click
from requests_toolbelt.sessions import BaseUrlSession

_DEFAULT_HOST = 'https://lagerdata.com'
_DEFAULT_WEBSOCKET_HOST = 'wss://ws.lagerdata.com'

def print_openocd_error(error):
    """
        Parse an openocd log file and print the error lines
    """
    if not error:
        return
    parsed = json.loads(error)
    logfile = parsed['logfile']
    if not logfile:
        return
    for line in logfile.splitlines():
        if 'Error: ' in line:
            click.secho(line, fg='red', err=True)

OPENOCD_ERROR_CODES = set((
    'openocd_start_failed',
))

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
            name = ctx.params['gateway'] or ctx.obj.default_gateway
            click.secho('You don\'t have a gateway with id `{}`'.format(name), fg='red', err=True)
            click.secho(
                'Please double check your login credentials and gateway id',
                fg='red',
                err=True,
            )
            ctx.exit(1)
        if r.status_code == 422:
            error = r.json()['error']
            if error['code'] in OPENOCD_ERROR_CODES:
                print_openocd_error(error['description'])
            else:
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

    @default_gateway.setter
    def default_gateway(self, gateway_id):
        self.defaults['gateway_id'] = str(gateway_id)

    def websocket_connection_params(self, socktype, **kwargs):
        """
            Yields a websocket connection to the given path
        """
        if socktype == 'job':
            path = f'/ws/job/{kwargs["job_id"]}'
        elif socktype == 'gdb-tunnel':
            path = f'/ws/gateway/{kwargs["gateway_id"]}/gdb-tunnel'
        else:
            raise ValueError(f'Invalid websocket type: {socktype}')
        uri = urllib.parse.urljoin(self.ws_host, path)

        headers = [
            (b'authorization', self.session.headers['Authorization'].encode()),
        ]
        ctx = get_ssl_context()

        return (uri, dict(extra_headers=headers, ssl_context=ctx))

def get_default_gateway(ctx):
    """
        Check for a default gateway in config; if not present, check if the user
        only has 1 gateway. If so, use that one.
    """
    name = ctx.obj.default_gateway
    if name is None:
        session = ctx.obj.session
        url = 'gateway/list'
        resp = session.get(url)
        resp.raise_for_status()
        gateways = resp.json()['gateways']

        if not gateways:
            click.secho('No gateways found! Please contact support@lagerdata.com', fg='red')
            ctx.exit(1)
        if len(gateways) == 1:
            ctx.obj.default_gateway = gateways[0]['id']
            return gateways[0]['id']

        hint = 'NAME. Set a default using `lager set default gateway <id>`'
        raise click.MissingParameter(
            param=ctx.command.params[0],
            param_hint=hint,
            ctx=ctx,
            param_type='argument',
        )
    return name

def get_ssl_context():
    """
        Get an SSL context, with custom CA cert if necessary
    """
    cafile_path = os.getenv('LAGER_CAFILE_PATH')
    if not cafile_path:
        # Use default system CA certs
        return None
    ctx = ssl.create_default_context()
    ctx.load_verify_locations(cafile=cafile_path)
    return ctx

def ensure_debugger_running(gateway, ctx):
    """
        Ensure debugger is running on a given gateway
    """
    session = ctx.obj.session
    url = 'gateway/{}/status'.format(gateway)
    gateway_status = session.get(url).json()
    if not gateway_status['running']:
        click.secho('Gateway debugger is not running. Please use `lager connect` to run it', fg='red', err=True)
        ctx.exit(1)