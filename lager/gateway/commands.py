"""
    lager.gateway.commands

    Gateway commands
"""
import itertools
import json
import click

def _get_default_gateway(ctx):
    name = ctx.obj.default_gateway
    if name is None:
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

def _handle_errors(resp, ctx):
    if resp.status_code == 404:
        name = ctx.params['name']
        click.secho('You don\'t have a gateway with id `{}`'.format(name), fg='red', err=True)
        click.secho(
            'Please double check your login credentials and gateway id',
            fg='red',
            err=True,
        )
        ctx.exit(1)
    if resp.status_code == 422:
        error = resp.json()['error']
        click.secho(error['description'], fg='red', err=True)
        ctx.exit(1)
    resp.raise_for_status()

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
    _handle_errors(resp, ctx)
    for device in resp.json()['devices']:
        click.echo('{vendor} {model}: {serial}'.format(**device))


@gateway.command()
@click.pass_context
@click.argument('name', required=False)
@click.option(
    '--hexfile',
    multiple=True, required=True, type=click.Path(exists=True),
    help='Hexfile(s) to flash. May be passed multiple times; files will be flashed in order.')
@click.option(
    '--serial',
    help='Serial number of device to flash. Required if multiple DUTs connected to gateway')
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
def flash(ctx, name, hexfile, serial, device, interface, speed, erase, baudrate, bytesize, parity, stopbits, xonxoff, rtscts, dsrdtr):
    """
        Flash gateway
    """
    if name is None:
        name = _get_default_gateway(ctx)

    session = ctx.obj.session
    url = 'gateway/{}/flash-duck'.format(name)
    files = list(zip(itertools.repeat('hexfile'), [open(path, 'rb') for path in hexfile]))
    if serial:
        files.append(('snr', serial))
    if erase:
        files.append(('erase', '1'))
    files.append(('device', device))
    files.append(('interface', interface))
    files.append(('speed', speed))
    serial_options = {
        'baudrate': baudrate,
        'bytesize': bytesize,
        'parity': parity,
        'stopbits': stopbits,
        'xonxoff': xonxoff,
        'rtscts': rtscts,
        'dsrdtr': dsrdtr,
    }
    files.append(('serial_options', json.dumps(serial_options)))

    resp = session.post(url, files=files, stream=True)
    _handle_errors(resp, ctx)
    dump_flash_output(resp, ctx)

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
