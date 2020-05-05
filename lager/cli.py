"""
    lager.cli

    Command line interface entry point
"""
import traceback
import os

import urllib3
import click
from requests_toolbelt.sessions import BaseUrlSession

from lager import __version__
from lager.context import LagerContext

from .gateway.commands import gateway
from .setter.commands import setter
from .lister.commands import lister
from .auth import load_auth
from .auth.commands import login, logout

_DEFAULT_HOST = 'https://lagerdata.com'

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
cli.add_command(setter)
cli.add_command(lister)
cli.add_command(login)
cli.add_command(logout)

def check_auth(ctx):
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

    verify = 'NOVERIFY' not in os.environ
    if not verify:
        urllib3.disable_warnings()

    host = os.getenv('LAGER_HOST', _DEFAULT_HOST)
    base_url = '{}{}'.format(host, '/api/v1/')
    session = BaseUrlSession(base_url=base_url)
    auth_header = {
        'Authorization': '{} {}'.format(auth['type'], auth['token'])
    }
    session.headers.update(auth_header)
    session.verify = verify

    ctx.obj = LagerContext(
        session=session,
    )
