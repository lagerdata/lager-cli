"""
    lager.connect.commands

    Commands for connecting to / disconnecting from DUT
"""
import click
from .. import SUPPORTED_DEVICES
from ..context import get_default_gateway

@click.command()
@click.pass_context
@click.option('--gateway', required=False, help='ID of gateway to which DUT is connected')
@click.option(
    '--snr',
    help='Serial number of device to connect. Required if multiple DUTs connected to gateway')
@click.option('--device', help='Target device type', type=click.Choice(SUPPORTED_DEVICES), required=True)
@click.option('--interface', help='Target interface', type=click.Choice(['ftdi', 'jlink', 'cmsis-dap', 'xds110']), default='ftdi', show_default=True)
@click.option('--transport', help='Target transport', type=click.Choice(['swd', 'jtag']), default='swd', show_default=True)
@click.option('--speed', help='Target interface speed in kHz', required=False, default='adaptive', show_default=True)
@click.option('--force', is_flag=True)
def connect(ctx, gateway, snr, device, interface, transport, speed, force):
    """
        Connect your gateway to your DUCK.
    """
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
