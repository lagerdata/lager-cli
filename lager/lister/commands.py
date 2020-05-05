"""
    lager.gateway.commands

    Gateway commands
"""
import click
from texttable import Texttable

@click.group(name='list')
def lister():
    """
        Lager list commands
    """
    pass


@lister.command()
@click.pass_context
def gateways(ctx):
    """
        List a user's gateways
    """

    url = 'gateway/list'
    session = ctx.obj.session
    resp = session.get(url)
    resp.raise_for_status()

    table = Texttable()
    table.set_deco(Texttable.HEADER)
    table.set_cols_dtype(['t', 'i'])
    table.set_cols_align(["l", "r"])
    table.add_row(['name', 'id'])

    for gateway in resp.json()['gateways']:
        table.add_row([gateway['name'], gateway['id']])
    print(table.draw())
