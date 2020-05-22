"""
    lager.cli

    Command line interface entry point
"""
import traceback
import click

from lager import __version__
from lager.config import read_config_file
from lager.context import LagerContext

from .gateway.commands import gateway
from .setter.commands import setter
from .lister.commands import lister
from .auth import load_auth
from .auth.commands import login, logout
from .job.commands import job


@click.group(invoke_without_command=True)
@click.pass_context
@click.option('--version', 'see_version', is_flag=True, help='See package version')
@click.option('--colorize', 'colorize', is_flag=True, help='Color output', default=False)
def cli(ctx=None, see_version=None, colorize=False):
    """
        Lager CLI
    """
    if see_version:
        click.echo(__version__)
        click.get_current_context().exit(0)
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
    else:
        if ctx.invoked_subcommand not in ('login', 'logout', 'set'):
            setup_context(ctx, colorize)

cli.add_command(gateway)
cli.add_command(setter)
cli.add_command(lister)
cli.add_command(login)
cli.add_command(logout)
cli.add_command(job)

def setup_context(ctx, colorize):
    """
        Ensure the user has a valid authorization
    """
    try:
        auth = load_auth()
    except Exception:  # pylint: disable=broad-except
        trace = traceback.format_exc()
        click.secho(trace, fg='red')
        click.echo('Something went wrong. Please run `lager logout` followed by `lager login`')
        click.echo('For additional assistance please send the above traceback (in red) to support@lagerdata.com')
        click.get_current_context().exit(0)

    if not auth:
        click.echo('Please login using `lager login` first')
        click.get_current_context().exit(0)

    config = read_config_file()
    ctx.obj = LagerContext(
        auth=auth,
        defaults=config['LAGER'],
        style=click.style if colorize else lambda string, **kwargs: string,
    )
