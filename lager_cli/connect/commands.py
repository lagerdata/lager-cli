"""
    lager.connect.commands

    Commands for connecting to / disconnecting from DUT
"""
import itertools
import click
from .. import SUPPORTED_DEVICES, SUPPORTED_INTERFACES
from ..context import get_default_gateway
from ..paramtypes import HexParamType, VarAssignmentType

@click.command()
@click.pass_context
@click.option('--gateway', required=False, help='ID of gateway to which DUT is connected')
@click.option(
    '--snr',
    help='Serial number of device to connect. Required if multiple DUTs connected to gateway')
@click.option('--device', help='Target device type', type=click.Choice(SUPPORTED_DEVICES), required=True)
@click.option('--interface', help='Target interface', type=click.Choice(SUPPORTED_INTERFACES), default='ftdi', show_default=True)
@click.option('--transport', help='Target transport', type=click.Choice(['swd', 'jtag']), default='swd', show_default=True)
@click.option('--speed', help='Target interface speed in kHz', required=False, default='adaptive', show_default=True)
@click.option('--workareasize', help='Set work area size. Useful for STM32 chips.', type=HexParamType(), required=False, default=None)
@click.option('--set', 'set_', multiple=True, type=VarAssignmentType(), help='Set debugger environment variable FOO to BAR')
@click.option('--force', is_flag=True, help='Disconnect debugger before reconnecting. If not set, connect will fail if debugger is already connected.')
def connect(ctx, gateway, snr, device, interface, transport, speed, workareasize, set_, force):
    """
        Connect your gateway to your DUCK.
    """
    set_ = list(set_)
    if workareasize:
        set_.append(['WORKAREASIZE', hex(workareasize)])
    if gateway is None:
        gateway = get_default_gateway(ctx)

    # Step one, try to start gdb on gateway
    files = []
    if snr:
        files.append(('snr', snr))
    files.append(('device', device))
    files.append(('interface', interface))
    files.append(('transport', transport))
    files.append(('speed', speed))
    files.append(('force', force))
    files.extend(
        zip(itertools.repeat('varnames'), [name for (name, _value) in set_])
    )
    files.extend(
        zip(itertools.repeat('varvalues'), [value for (_name, value) in set_])
    )

    session = ctx.obj.session
    session.start_debugger(gateway, files=files)
    click.secho('Connected!', fg='green')


@click.command()
@click.pass_context
@click.option('--gateway', required=False, help='ID of gateway to which DUT is connected')
def disconnect(ctx, gateway):
    """
        Disconnect your gateway from your DUCK.
    """
    if gateway is None:
        gateway = get_default_gateway(ctx)

    session = ctx.obj.session
    session.stop_debugger(gateway)
    click.secho('Disconnected!', fg='green')
