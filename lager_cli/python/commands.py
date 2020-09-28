"""
    lager.flash.commands

    Commands for flashing a DUT
"""
import os
import itertools
import functools
import click
from ..context import get_default_gateway
from ..util import stream_python_output, zip_dir, SizeLimitExceeded
from ..paramtypes import EnvVarType

MAX_ZIP_SIZE = 10_000_000  # Max size of zipped folder in bytes

@click.command()
@click.pass_context
@click.argument('runnable', required=True, type=click.Path(exists=True))
@click.option('--gateway', required=False, help='ID of gateway to which DUT is connected')
@click.option('--image', default='lagerdata/gatewaypy3:v0.1.37', help='Docker image to use for running script')
@click.option(
    '--env',
    multiple=True, type=EnvVarType(), help='Environment variables to set for the python script. '
    'Format is `--env FOO=BAR` - this will set an environment varialbe named `FOO` to the value `BAR`')
@click.option(
    '--passenv',
    multiple=True, help='Environment variables to inherit from the current environment and pass to the python script. '
    'This option is useful for secrets, tokens, passwords, or any other values that you do not want to appear on the '
    'command line. Example: `--passenv FOO` will set an environment variable named `FOO` in the python script to the value'
    'of `FOO` in the current environment.')
@click.option('--kill', is_flag=True, default=False, help='Terminate a running python script')
@click.option('--timeout', type=click.INT, required=False, help='Max runtime in seconds for the python script')
def python(ctx, runnable, gateway, image, env, passenv, kill, timeout):
    """
        Run a python script on the gateway
    """
    session = ctx.obj.session
    if gateway is None:
        gateway = get_default_gateway(ctx)

    if kill:
        resp = session.kill_python(gateway).json()
        resp.raise_for_status()
        return

    post_data = [
        ('image', image),
    ]
    post_data.extend(
        zip(itertools.repeat('env'), env)
    )
    post_data.extend(
        zip(itertools.repeat('env'), [f'{name}={os.environ[name]}' for name in passenv])
    )

    if timeout is not None:
        post_data.append(('timeout', timeout))

    if os.path.isfile(runnable):
        post_data.append(('script', open(runnable, 'rb')))
    elif os.path.isdir(runnable):
        try:
            max_content_size = 20_000_000
            zipped_folder = zip_dir(runnable, max_content_size=max_content_size)
        except SizeLimitExceeded:
            click.secho(f'Folder content exceeds max size of {max_content_size:,} bytes', err=True, fg='red')
            ctx.exit(1)

        if len(zipped_folder) > MAX_ZIP_SIZE:
            click.secho(f'Zipped module content exceeds max size of {MAX_ZIP_SIZE:,} bytes', err=True, fg='red')
            ctx.exit(1)

        post_data.append(('module', zipped_folder))

    resp = session.run_python(gateway, files=post_data)
    kill_python = functools.partial(session.kill_python, gateway)
    stream_python_output(resp, kill_python)
