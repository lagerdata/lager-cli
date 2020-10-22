"""
    lager.canbus.commands

    Commands for canbus
"""
import click
import json
from ..context import get_default_gateway
from ..paramtypes import CanFrameType

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

@canbus.command()
@click.pass_context
@click.option('--gateway', required=False, help='ID of gateway to which DUT is connected')
@click.argument('can_frames', required=True, nargs=-1, type=CanFrameType())
def send(ctx, gateway, can_frames):
    """
        Send a frame on the CAN bus

        CAN_FRAME format:

        \b
        <can_id>#{R|data}
            for CAN 2.0 frames

        \b
        <can_id>##<flags>{data}
            for CAN FD frames

        \b
        <can_id>:
            can have 3 (SFF) or 8 (EFF) hex chars

        \b
        {data}:
            has 0..8 (0..64 CAN FD) ASCII hex-values (optionally separated by '.')

        \b
        <flags>:
            a single ASCII Hex value (0 .. F) which defines canfd_frame.flags

        \b
        CAN_FRAME Examples:
            5A1#11.2233.44556677.88 / 123#DEADBEEF / 5AA# / 123##1 / 213##311
            1F334455#1122334455667788 / 123#R for remote transmission request.
    """

    if gateway is None:
        gateway = get_default_gateway(ctx)

    session = ctx.obj.session
    resp = session.can_send(gateway, can_frames)
    print(resp.json())

