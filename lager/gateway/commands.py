"""
    lager.gateway.commands

    Gateway commands
"""
import collections
import os
import click
import trio
import trio_websocket
from .. import SUPPORTED_DEVICES
from ..status import run_job_output
from .tunnel import serve_tunnel
from ..context import get_default_gateway

@click.group()
def gateway():
    """
        Lager gateway commands
    """
    pass

@gateway.command()
@click.pass_context
@click.argument('name', required=False)
def hello(ctx, name):
    """
        Say hello to gateway
    """
    if name is None:
        name = get_default_gateway(ctx)
    session = ctx.obj.session
    url = 'gateway/{}/hello'.format(name)
    resp = session.get(url)
    click.echo(resp.content, nl=False)

@gateway.command()
@click.pass_context
@click.argument('name', required=False)
@click.option('--model', required=False)
def serial_numbers(ctx, name, model):
    """
        Get serial numbers of devices attached to gateway
    """
    if name is None:
        name = get_default_gateway(ctx)

    session = ctx.obj.session
    url = 'gateway/{}/serial-numbers'.format(name)
    resp = session.get(url, params={'model': model})
    for device in resp.json()['devices']:
        device['serial'] = device['serial'].lstrip('0')
        click.echo('{vendor} {model}: {serial}'.format(**device))

@gateway.command()
@click.pass_context
@click.argument('name', required=False)
def serial_ports(ctx, name):
    """
        Get serial ports attached to gateway
    """
    if name is None:
        name = get_default_gateway(ctx)

    session = ctx.obj.session
    url = 'gateway/{}/serial-ports'.format(name)
    resp = session.get(url)
    style = ctx.obj.style
    for port in resp.json()['serial_ports']:
        click.echo('{} - {}'.format(style(port['device'], fg='green'), port['description']))

class HexParamType(click.ParamType):
    """
        Hexadecimal integer parameter
    """
    name = 'hex'

    def convert(self, value, param, ctx):
        """
            Parse string reprsentation of a hex integer
        """
        try:
            return int(value, 16)
        except ValueError:
            self.fail(f"{value} is not a valid hex integer", param, ctx)

    def __repr__(self):
        return 'HEX'

Binfile = collections.namedtuple('Binfile', ['path', 'address'])
class BinfileType(click.ParamType):
    """
        Type to represent a command line argument for a binfile (<path>,<address>)
    """
    envvar_list_splitter = os.path.pathsep
    name = 'binfile'

    def __init__(self, *args, exists=False, **kwargs):
        self.exists = exists
        super().__init__(*args, **kwargs)

    def convert(self, value, param, ctx):
        """
            Convert binfile param string into useable components
        """
        parts = value.rsplit(',', 1)
        if len(parts) != 2:
            self.fail(f'{value}. Syntax: --binfile <filename>,<address>', param, ctx)
        filename, address = parts
        path = click.Path(exists=self.exists).convert(filename, param, ctx)
        address = HexParamType().convert(address, param, ctx)

        return Binfile(path=path, address=address)

    def __repr__(self):
        return 'BINFILE'

@gateway.command()
@click.pass_context
@click.argument('name', required=False)
@click.option('--message-timeout', default=5*60,
              help='Max time in seconds to wait between messages from API.'
              'This timeout only affects reading output and does not cancel the actual test run if hit.')
@click.option('--overall-timeout', default=30*60,
              help='Cumulative time in seconds to wait for session output.'
              'This timeout only affects reading output and does not cancel the actual test run if hit.')
def erase(ctx, name, message_timeout, overall_timeout):
    if name is None:
        name = get_default_gateway(ctx)

    ensure_running(name, ctx)

    session = ctx.obj.session
    url = 'gateway/{}/erase-duck'.format(name)
    resp = session.post(url, stream=True)
    test_run = resp.json()
    job_id = test_run['test_run']['id']
    click.echo('Job id: {}'.format(job_id))
    connection_params = ctx.obj.websocket_connection_params(socktype='job', job_id=job_id)
    run_job_output(connection_params, None, message_timeout, overall_timeout, ctx.obj.debug)

@gateway.command()
@click.pass_context
@click.argument('name', required=False)
def jobs(ctx, name):
    """
        Get serial ports attached to gateway
    """
    if name is None:
        name = get_default_gateway(ctx)

    session = ctx.obj.session
    url = 'gateway/{}/jobs'.format(name)
    resp = session.get(url)
    print(resp.json())

def ensure_running(name, ctx):
    session = ctx.obj.session
    url = 'gateway/{}/status'.format(name)
    gateway_status = session.get(url).json()
    if not gateway_status['running']:
        click.secho('Gateway debugger is not running. Please use `lager connect` to run it', fg='red', err=True)
        ctx.exit(1)

@gateway.command()
@click.pass_context
@click.argument('name', required=False)
@click.option('--host', default='localhost', help='interface for gdbserver to bind. '
              'Use --host \'*\' to bind to all interfaces.')
@click.option('--port', default=3333, help='Port for gdbserver')
def gdbserver(ctx, name, host, port):
    """
        Run GDB server on gateway. By default binds to localhost, meaning gdb client connections
        must originate from the machine running `lager gdbserver`. If you would like to bind to
        all interfaces, use --host '*'
    """
    if name is None:
        name = get_default_gateway(ctx)

    ensure_running(name, ctx)

    connection_params = ctx.obj.websocket_connection_params(socktype='gdb-tunnel', gateway_id=name)
    try:
        trio.run(serve_tunnel, host, port, connection_params)
    except PermissionError as exc:
        if port < 1024:
            click.secho(f'Permission denied for port {port}. Using a port number less than '
                        '1024 typically requires root privileges.', fg='red', err=True)
        else:
            click.secho(str(exc), fg='red', err=True)
        if ctx.obj.debug:
            raise
    except OSError as exc:
        click.secho(f'Could not start gdbserver on port {port}: {exc}', fg='red', err=True)
        if ctx.obj.debug:
            raise

@gateway.command()
@click.pass_context
@click.argument('name', required=False)
@click.option(
    '--snr',
    help='Serial number of device to connect. Required if multiple DUTs connected to gateway')
@click.option('--device', help='Target device type', type=click.Choice(SUPPORTED_DEVICES), required=True)
@click.option('--interface', help='Target interface', type=click.Choice(['ftdi', 'jlink', 'cmsis-dap']), default='ftdi')
@click.option('--transport', help='Target transport', type=click.Choice(['swd', 'jtag']), default='swd')
@click.option('--speed', help='Target interface speed in kHz', required=False, default='adaptive')
@click.option('--force', is_flag=True)
@click.option('--debugger', default='openocd', help='Debugger to use for device flashing')
def connect(ctx, name, snr, device, interface, transport, speed, force, debugger):
    """
        Connect your gateway to your DUCK.
    """
    if name is None:
        name = get_default_gateway(ctx)

    # Step one, try to start gdb on gateway
    session = ctx.obj.session
    url = 'gateway/{}/start-debugger'.format(name)
    files = []
    if snr:
        files.append(('snr', snr))
    files.append(('device', device))
    files.append(('interface', interface))
    files.append(('transport', transport))
    files.append(('speed', speed))
    files.append(('debugger', debugger))
    files.append(('force', force))

    session.post(url, files=files)
    click.secho('Connected!', fg='green')


@gateway.command()
@click.pass_context
@click.argument('name', required=False)
@click.option('--debugger', default='openocd', help='Debugger to use for device flashing')
def disconnect(ctx, name, debugger):
    """
        Disconnect your gateway from your DUCK.
    """
    if name is None:
        name = get_default_gateway(ctx)

    # stop debubber
    session = ctx.obj.session
    url = 'gateway/{}/stop-debugger'.format(name)
    files = []
    files.append(('debugger', debugger))

    session.post(url, files=files)
    click.secho('Disconnected!', fg='green')

@gateway.command()
@click.pass_context
@click.argument('name', required=False)
def status(ctx, name):
    """
        Disconnect your gateway from your DUCK.
    """
    if name is None:
        name = get_default_gateway(ctx)

    # stop debubber
    session = ctx.obj.session
    url = 'gateway/{}/status'.format(name)

    response = session.get(url).json()
    running = response['running']
    cmdline = response['cmdline']
    logfile = response['logfile']
    click.echo(f'Debugger running: {running}')
    if cmdline:
        click.echo('---- Debugger config ----')
        config = cmdline[3:-1]
        for i in range(0, len(config), 2):
            chunk = config[i:i+2]
            if chunk[0] == '-f':
                parts = chunk[1].split('/')
                click.echo(f'{parts[0]}: {parts[-1].rstrip(".cfg")}')
            elif chunk[0] == '-c':
                click.echo(chunk[1])

    if logfile:
        click.echo('---- Logs ----')
        click.echo(logfile)
