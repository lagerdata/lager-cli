"""
    lager.canbus.commands

    Commands for canbus
"""
import itertools
import click
from ..context import get_default_gateway

@click.group(name='canbus')
def canbus():
    """
        Lager canbus commands
    """
    pass
@canbus.command()
@click.pass_context
@click.option('--gateway', required=False, help='ID of gateway to which DUT is connected')
@click.option('--bitrate', required=True, type=click.INT, help='bus bitrate')
def up(ctx, gateway, bitrate):
    """
        Bring up the CAN bus
    """
    if gateway is None:
        gateway = get_default_gateway(ctx)

    session = ctx.obj.session
    resp = session.can_up(gateway, bitrate)
    print(resp.json())
