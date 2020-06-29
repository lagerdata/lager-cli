"""
    lager.erase.commands

    Commands for erasing a DUT
"""
import click
from ..context import get_default_gateway, MemoryAddressType

@click.command()
@click.pass_context
@click.option('--gateway', required=False, help='ID of gateway to which DUT is connected')
@click.argument('start_addr', type=MemoryAddressType())
@click.argument('end_addr', type=MemoryAddressType())
def erase(ctx, gateway, start_addr, end_addr):
    """
        Erase DUT
    """
    if gateway is None:
        gateway = get_default_gateway(ctx)

    session = ctx.obj.session
    url = 'gateway/{}/erase-duck'.format(gateway)
    addresses = dict(start_addr=start_addr, end_addr=end_addr)
    resp = session.post(url, json=addresses)
    for chunk in resp.iter_content(chunk_size=8):
        click.echo(chunk, nl=False)
