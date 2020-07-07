"""
    lager.erase.commands

    Commands for erasing a DUT
"""
import click
from ..context import get_default_gateway
from ..paramtypes import MemoryAddressType
from ..util import stream_output

@click.command()
@click.pass_context
@click.option('--gateway', required=False, help='ID of gateway to which DUT is connected')
@click.argument('start_addr', type=MemoryAddressType())
@click.argument('length', type=MemoryAddressType())
def erase(ctx, gateway, start_addr, length):
    """
        Erase DUT
    """
    if gateway is None:
        gateway = get_default_gateway(ctx)

    session = ctx.obj.session
    url = 'gateway/{}/erase-duck'.format(gateway)
    addresses = dict(start_addr=start_addr, length=length)
    resp = session.post(url, json=addresses)
    stream_output(resp)
