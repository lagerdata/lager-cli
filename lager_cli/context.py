"""
    lager.context

    CLI context management
"""
from enum import Enum
import functools
import os
import json
import ssl
import urllib.parse
import urllib3
import requests
import click
from requests_toolbelt.sessions import BaseUrlSession

_DEFAULT_HOST = 'https://app.lagerdata.com'
_DEFAULT_WEBSOCKET_HOST = 'wss://app.lagerdata.com'

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

def quote(gateway):
    return urllib.parse.quote(str(gateway), safe='')

class LagerSession(BaseUrlSession):
    """
        requests session wrapper
    """

    @staticmethod
    def handle_errors(ctx, r, *args, **kwargs):
        """
            Handle request errors
        """
        try:
            current_context = click.get_current_context()
            ctx = current_context
        except RuntimeError:
            pass
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

    def __init__(self, ctx, auth, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._connection_exception = None
        verify = 'NOVERIFY' not in os.environ
        if not verify:
            urllib3.disable_warnings()

        if auth:
            auth_header = {
                'Authorization': '{} {}'.format(auth['type'], auth['token'])
            }
            self.headers.update(auth_header)
        self.verify = verify
        self.hooks['response'].append(functools.partial(LagerSession.handle_errors, ctx))


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

    def start_debugger(self, gateway, files):
        """
            Start the debugger on the gateway
        """
        url = 'gateway/{}/start-debugger'.format(quote(gateway))
        return self.post(url, files=files)

    def stop_debugger(self, gateway):
        """
            Stop the debugger on the gateway
        """
        url = 'gateway/{}/stop-debugger'.format(quote(gateway))
        return self.post(url)

    def erase_dut(self, gateway, addresses):
        """
            Erase DUT connected to gateway
        """
        url = 'gateway/{}/erase-duck'.format(quote(gateway))
        return self.post(url, json=addresses)

    def flash_dut(self, gateway, files):
        """
            Flash DUT connected to gateway
        """
        url = 'gateway/{}/flash-duck'.format(quote(gateway))
        return self.post(url, files=files, stream=True)

    def gateway_hello(self, gateway):
        """
            Say hello to gateway to see if it is connected
        """
        url = 'gateway/{}/hello'.format(quote(gateway))
        return self.get(url)

    def serial_numbers(self, gateway, model):
        """
            Get serial numbers of devices attached to gateway
        """
        url = 'gateway/{}/serial-numbers'.format(quote(gateway))
        return self.get(url, params={'model': model})

    def serial_ports(self, gateway):
        """
            Get serial port devices attached to gateway
        """
        url = 'gateway/{}/serial-ports'.format(quote(gateway))
        return self.get(url)

    def gateway_status(self, gateway):
        """
            Get debugger status on gateway
        """
        url = 'gateway/{}/status'.format(quote(gateway))
        return self.get(url)

    def list_gateways(self):
        """
            Get all gateways for logged-in user
        """
        url = 'gateway/list'
        return self.get(url)

    def reset_dut(self, gateway, halt):
        """
            Reset the DUT attached to a gateway and optionally halt it
        """
        url = 'gateway/{}/reset-duck'.format(quote(gateway))
        return self.post(url, json={'halt': halt})

    def run_dut(self, gateway):
        """
            Run the DUT attached to a gateway
        """
        url = 'gateway/{}/run-duck'.format(quote(gateway))
        return self.post(url, stream=True)

    def uart_gateway(self, gateway, serial_options, test_runner):
        """
            Open a connection to gateway serial port
        """
        url = 'gateway/{}/uart-duck'.format(quote(gateway))

        if test_runner == 'none':
            test_runner = None
        json_data = {
            'serial_options': serial_options,
            'test_runner': test_runner,
        }
        return self.post(url, json=json_data)

    def rename_gateway(self, gateway, new_name):
        """
            Rename a gateway
        """
        url = 'gateway/{}/rename'.format(quote(gateway))
        return self.post(url, json={'name': new_name})

    def start_local_gdb_tunnel(self, gateway, fork):
        """
            Start the local gdb tunnel on gateway
        """
        url = 'gateway/{}/local-gdb'.format(quote(gateway))
        return self.post(url, json={'fork': fork})

    def gpio_set(self, gateway, gpio, type_, pull):
        """
            Set a GPIO pin to input or output
        """
        url = 'gateway/{}/gpio/set'.format(quote(gateway))
        return self.post(url, json={'gpio': gpio, 'type': type_, 'pull': pull})

    def gpio_input(self, gateway, gpio):
        """
            Read from the GPIO pin
        """
        url = 'gateway/{}/gpio/input'.format(quote(gateway))
        return self.post(url, json={'gpio': gpio})

    def gpio_output(self, gateway, gpio, level):
        """
            Write to the GPIO pin
        """
        url = 'gateway/{}/gpio/output'.format(quote(gateway))
        return self.post(url, json={'gpio': gpio, 'level': level})

    def gpio_servo(self, gateway, gpio, pulsewidth, stop):
        """
            Control a servo with GPIO
        """
        url = 'gateway/{}/gpio/servo'.format(quote(gateway))
        return self.post(url, json={'gpio': gpio, 'pulsewidth': pulsewidth, 'stop': stop})

    def gpio_trigger(self, gateway, gpio, pulse_length, level):
        """
            Send a trigger pulse on GPIO
        """
        url = 'gateway/{}/gpio/trigger'.format(quote(gateway))
        return self.post(url, json={'gpio': gpio, 'pulse_length': pulse_length, 'level': level})

    def gpio_hardware_pwm(self, gateway, frequency, dutycycle):
        """
            Start hardware PWM on gpio
        """
        url = 'gateway/{}/gpio/hardware-pwm'.format(quote(gateway))
        return self.post(url, json={'frequency': frequency, 'dutycycle': dutycycle})

    def gpio_hardware_clock(self, gateway, frequency):
        """
            Start hardware clock on gpio
        """
        url = 'gateway/{}/gpio/hardware-clock'.format(quote(gateway))
        return self.post(url, json={'frequency': frequency})

class LagerContext:  # pylint: disable=too-few-public-methods
    """
        Lager Context manager
    """
    def __init__(self, ctx, auth, defaults, debug, style):
        host = os.getenv('LAGER_HOST', _DEFAULT_HOST)
        ws_host = os.getenv('LAGER_WS_HOST', _DEFAULT_WEBSOCKET_HOST)
        base_url = '{}{}'.format(host, '/api/v1/')

        self.session = LagerSession(ctx, auth, base_url=base_url)
        self.defaults = defaults
        self.style = style
        self.ws_host = ws_host
        self.debug = debug
        if auth:
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
    name = os.getenv('LAGER_GATEWAY')
    if name is None:
        name = ctx.obj.default_gateway

    if name is None:
        session = ctx.obj.session
        resp = session.list_gateways()
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
    gateway_status = session.gateway_status(gateway).json()
    if not gateway_status['running']:
        click.secho('Gateway debugger is not running. Please use `lager connect` to run it', fg='red', err=True)
        ctx.exit(1)

class CIEnvironment(Enum):
    """
        Enum representing supported CI system
    """
    HOST = 'host'
    DRONE = 'drone'

def get_ci_environment():
    """
        Determine what CI environment, if any, we are running in
    """

    if os.getenv('DRONE') == 'true':
        return CIEnvironment.DRONE
    return CIEnvironment.HOST
