"""
    lager.gateway.commands

    Gateway commands
"""

import click

@click.group()
def gateway():
    """
        Lager gateway commands
    """
    pass

@gateway.command()
@click.argument('name')
@click.argument('hexfile')
def flash(name, hexfile):
    """
        Flash gateway
    """
    click.echo('Todo: Flash')
