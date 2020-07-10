"""
    lager.connect.commands

    Commands for connecting to / disconnecting from DUT
"""
import click
from .. import SUPPORTED_DEVICES
from ..context import get_default_gateway

@click.command()
@click.pass_context
@click.argument('name', required=False)
@click.option(
    '--snr',
    help='Serial number of device to connect. Required if multiple DUTs connected to gateway')
@click.option('--device', help='Target device type', type=click.Choice(SUPPORTED_DEVICES), required=True)
@click.option('--interface', help='Target interface', type=click.Choice(['ftdi', 'jlink', 'cmsis-dap', 'xds110']), default='ftdi')
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


@click.command()
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
