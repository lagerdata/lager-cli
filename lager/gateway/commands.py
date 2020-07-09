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
