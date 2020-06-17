"""
    lager.gateway.commands

    Gateway commands
"""
import itertools
import json
import collections
import os
import click
import trio
import trio_websocket
from lager.status import run_job_output
from lager.gateway.tunnel import serve_tunnel

def _get_default_gateway(ctx):
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
        name = _get_default_gateway(ctx)
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
        name = _get_default_gateway(ctx)

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
        name = _get_default_gateway(ctx)

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
@click.option(
    '--snr',
    help='Serial number of device to flash. Required if multiple DUTs connected to gateway')
@click.option('--device', help='Target device type', required=True)
@click.option('--interface', help='Target interface', required=True)
@click.option('--speed', help='Target interface speed in kHz', required=False, default='adaptive')
@click.option('--force', is_flag=True)
@click.option('--debugger', default='openocd', help='Debugger to use for device flashing')
@click.option('--message-timeout', default=5*60,
              help='Max time in seconds to wait between messages from API.'
              'This timeout only affects reading output and does not cancel the actual test run if hit.')
@click.option('--overall-timeout', default=30*60,
              help='Cumulative time in seconds to wait for session output.'
              'This timeout only affects reading output and does not cancel the actual test run if hit.')
def erase(ctx, name, snr, device, interface, speed, force, debugger, message_timeout, overall_timeout):
    if name is None:
        name = _get_default_gateway(ctx)

    session = ctx.obj.session
    url = 'gateway/{}/erase-duck'.format(name)
    files = []
    if snr:
        files.append(('snr', snr))
    files.append(('device', device))
    files.append(('interface', interface))
    files.append(('speed', speed))
    files.append(('debugger', debugger))
    if force:
        files.append(('force', '1'))

    resp = session.post(url, files=files, stream=True)
    test_run = resp.json()
    job_id = test_run['test_run']['id']
    click.echo('Job id: {}'.format(job_id))
    connection_params = ctx.obj.websocket_connection_params(socktype='job', job_id=job_id)
    run_job_output(connection_params, message_timeout, overall_timeout, ctx.obj.debug)

@gateway.command()
@click.pass_context
@click.argument('name', required=False)
@click.option(
    '--hexfile',
    multiple=True, type=click.Path(exists=True),
    help='Hexfile(s) to flash. May be passed multiple times; files will be flashed in order.')
@click.option(
    '--binfile',
    multiple=True, type=BinfileType(exists=True),
    help='Binfile(s) to flash. Syntax: --binfile `<filename>,<address>` May be passed multiple times; files will be flashed in order.')
@click.option(
    '--snr',
    help='Serial number of device to flash. Required if multiple DUTs connected to gateway')
@click.option('--serial-device', help='Gateway serial port device')
@click.option('--device', help='Target device type', required=True)
@click.option('--interface', help='Target interface', required=True)
@click.option('--speed', help='Target interface speed in kHz', required=False, default='adaptive')
@click.option('--erase/--no-erase', help='Erase target before flashing', default=True)
@click.option('--baudrate', help='Serial baud rate', type=int, default=None)
@click.option('--bytesize', help='Number of data bits', type=click.Choice(['5', '6', '7', '8']), default=None)
@click.option('--parity', help='Parity check', type=click.Choice(['none', 'even', 'odd', 'mark', 'space']), default=None)
@click.option('--stopbits', help='Number of stop bits', type=click.Choice(['1', '1.5', '2']), default=None)
@click.option('--xonxoff/--no-xonxoff', default=None, help='Enable/disable software XON/XOFF flow control')
@click.option('--rtscts/--no-rtscts', default=None, help='Enable/disable hardware RTS/CTS flow control')
@click.option('--dsrdtr/--no-dsrdtr', default=None, help='Enable/disable hardware DSR/DTR flow control')
@click.option('--force', is_flag=True)
@click.option('--follow/--no-follow', default=False, help='Display job output')
@click.option('--debugger', default='openocd', help='Debugger to use for device flashing')
@click.option('--message-timeout', default=5*60,
              help='Max time in seconds to wait between messages from API.'
              'This timeout only affects reading output and does not cancel the actual test run if hit.')
@click.option('--overall-timeout', default=30*60,
              help='Cumulative time in seconds to wait for session output.'
              'This timeout only affects reading output and does not cancel the actual test run if hit.')
def flash(ctx, name, hexfile, binfile, snr, serial_device, device, interface, speed, erase,
            baudrate, bytesize, parity, stopbits, xonxoff, rtscts, dsrdtr, force, follow, debugger,
            message_timeout, overall_timeout):
    """
        Flash gateway
    """
    if xonxoff and rtscts:
        raise click.UsageError(
            'Cannot use xonxoff and rtscts simultaneously',
            ctx=ctx,
        )

    if name is None:
        name = _get_default_gateway(ctx)

    session = ctx.obj.session
    url = 'gateway/{}/flash-duck'.format(name)
    files = list(zip(itertools.repeat('hexfile'), [open(path, 'rb') for path in hexfile]))
    files.extend(
        zip(itertools.repeat('binfile'), [open(binf.path, 'rb') for binf in binfile])
    )
    files.extend(
        zip(itertools.repeat('binfile_address'), [binf.address for binf in binfile])
    )
    if snr:
        files.append(('snr', snr))
    if erase:
        files.append(('erase', '1'))
    files.append(('device', device))
    files.append(('interface', interface))
    files.append(('speed', speed))
    files.append(('debugger', debugger))
    serial_options = {
        'device': serial_device,
        'baudrate': baudrate,
        'bytesize': bytesize,
        'parity': parity,
        'stopbits': stopbits,
        'xonxoff': xonxoff,
        'rtscts': rtscts,
        'dsrdtr': dsrdtr,
    }
    files.append(('serial_options', json.dumps(serial_options)))
    if force:
        files.append(('force', '1'))

    resp = session.post(url, files=files, stream=True)
    test_run = resp.json()
    if follow:
        job_id = test_run['test_run']['id']
        click.echo('Job id: {}'.format(job_id))
        connection_params = ctx.obj.websocket_connection_params(socktype='job', job_id=job_id)
        run_job_output(connection_params, message_timeout, overall_timeout, ctx.obj.debug)
    else:
        click.echo(test_run)

def dump_flash_output(resp, ctx):
    """
        Stream flash response output
    """
    style = ctx.obj.style
    separator = None
    in_tests = False
    has_fail = False
    in_summary = False
    summary_separator = '-----------------------'
    for line in resp.iter_lines(chunk_size=8):
        if separator is None:
            separator = line
            continue
        if line == separator:
            in_tests = True
            continue
        line = line.decode()
        if not in_tests:
            click.echo(line)
        else:
            if line == summary_separator:
                in_summary = True
                click.echo(line)
                continue
            if in_summary:
                color = 'red' if has_fail else 'green'
                click.echo(style(line, fg=color))
            else:
                if ':FAIL' in line:
                    has_fail = True
                    click.echo(style(line, fg='red'))
                elif ':PASS' in line:
                    click.echo(style(line, fg='green'))
                elif ':INFO' in line:
                    click.echo(style(line, fg='yellow'))
                else:
                    click.echo(line)
    if has_fail:
        ctx.exit(1)


@gateway.command()
@click.pass_context
@click.argument('name', required=False)
def jobs(ctx, name):
    """
        Get serial ports attached to gateway
    """
    if name is None:
        name = _get_default_gateway(ctx)

    session = ctx.obj.session
    url = 'gateway/{}/jobs'.format(name)
    resp = session.get(url)
    print(resp.json())

@gateway.command()
@click.pass_context
@click.argument('name', required=False)
@click.option(
    '--snr',
    help='Serial number of device to debug. Required if multiple DUTs connected to gateway')
@click.option('--device', help='Target device type', required=True)
@click.option('--interface', help='Target interface', required=True)
@click.option('--speed', help='Target interface speed in kHz', required=False, default='adaptive')
@click.option('--debugger', default='openocd', help='Debugger to use for device flashing')
@click.option('--host', default='localhost', help='Host bind for gdb tunnel')
@click.option('--port', default=2159, help='Port for gdb tunnel')
def gdb_tunnel(ctx, name, snr, device, interface, speed, debugger, host, port):
    """
        GDB tunnel to gateway
    """
    if name is None:
        name = _get_default_gateway(ctx)

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
        click.secho(f'Could not start gdb-tunnel on port {port}: {exc}', fg='red', err=True)
        if ctx.obj.debug:
            raise
