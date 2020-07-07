"""
    lager.cli

    Command line interface entry point
"""
import traceback
import click

from . import __version__
from .config import read_config_file
from .context import LagerContext

from .gateway.commands import gateway
from .setter.commands import setter
from .lister.commands import lister
from .auth import load_auth
from .auth.commands import login, logout
from .job.commands import job
from .devenv.commands import devenv
from .exec.commands import exec_
from .flash.commands import flash
from .run.commands import run
from .erase.commands import erase
from .reset.commands import reset
from .uart.commands import uart
from .testrun.commands import testrun

@click.group(invoke_without_command=True)
@click.pass_context
@click.option('--version', 'see_version', is_flag=True, help='See package version')
@click.option('--debug', 'debug', is_flag=True, help='Show debug output', default=False)
@click.option('--colorize', 'colorize', is_flag=True, help='Color output', default=False)
def cli(ctx=None, see_version=None, debug=False, colorize=False):
    """
        Lager CLI
    """
    if see_version:
        click.echo(__version__)
        click.get_current_context().exit(0)
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
    else:
        if ctx.invoked_subcommand not in ('login', 'logout', 'set', 'devenv', 'exec'):
            setup_context(ctx, debug, colorize)

cli.add_command(gateway)
cli.add_command(setter)
cli.add_command(lister)
cli.add_command(login)
cli.add_command(logout)
cli.add_command(job)
cli.add_command(devenv)
cli.add_command(exec_)
cli.add_command(flash)
cli.add_command(run)
cli.add_command(erase)
cli.add_command(reset)
cli.add_command(uart)
cli.add_command(testrun)

def setup_context(ctx, debug, colorize):
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
        debug=debug,
        style=click.style if colorize else lambda string, **kwargs: string,
    )
