"""
    lager.erase.commands

    Commands for erasing a DUT
"""
import click
from ..context import get_default_gateway, MemoryAddressType
from ..util import stream_output

@click.command()
@click.pass_context
@click.option('--gateway', required=False, help='ID of gateway to which DUT is connected')
@click.option('--halt', is_flag=True, help='Halt the DUT after reset. Default: do not halt', default=False)
def reset(ctx, gateway, halt):
    """
        Reset the DUT. By default will not halt the DUT; use `lager reset --halt` to reset and halt.
    """
    if gateway is None:
        gateway = get_default_gateway(ctx)
    session = ctx.obj.session
    url = 'gateway/{}/reset-duck'.format(gateway)
    resp = session.post(url, json={'halt': halt})
    stream_output(resp)
