"""
    lager.cli

    Command line interface entry point
"""
import os
import configparser
import click
from lager import __version__

from .gateway.commands import gateway
from .auth import load_auth
from .auth.commands import login, logout

@click.group(invoke_without_command=True)
@click.pass_context
@click.option('--version', 'see_version', is_flag=True, help='See package version')
def cli(ctx, see_version):
    """
        Lager CLI
    """
    if see_version:
        click.echo(__version__)
        click.get_current_context().exit(0)
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
    else:
        if ctx.invoked_subcommand not in ('login', 'logout'):
            check_auth(ctx)

cli.add_command(gateway)
cli.add_command(login)
cli.add_command(logout)

def check_auth(ctx):
    ctx.obj = load_auth()
    if not ctx.obj:
        click.echo('Please login using `lager login` first')
        click.get_current_context().exit(0)
