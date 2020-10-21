"""
    lager.canbus.commands

    Commands for canbus
"""
import click
from ..context import get_default_gateway

@click.group(name='canbus')
def canbus():
    """
        Lager CAN Bus commands
    """
    pass
@canbus.command()
@click.pass_context
@click.option('--gateway', required=False, help='ID of gateway to which DUT is connected')
@click.option('--bitrate', required=True, type=click.INT, help='bus bitrate e.g. 500000, 250000, etc')
def up(ctx, gateway, bitrate):
    """
        Bring up the CAN Bus at the specified bitrate
    """
    if gateway is None:
        gateway = get_default_gateway(ctx)

    session = ctx.obj.session
    resp = session.can_up(gateway, bitrate)
    print(resp.json())
