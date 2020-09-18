"""
    lager.flash.commands

    Commands for flashing a DUT
"""
import os
import itertools
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED
from io import BytesIO
import pathlib
import functools
import click
from ..context import get_default_gateway
from ..util import stream_python_output
from ..paramtypes import EnvVarType

def handle_error(error):
    """
        os.walk error handler, just raise it
    """
    raise error

def zip_dir(root):
    """
        Zip a directory into memory
    """
    rootpath = pathlib.Path(root)
    exclude = ['.git']
    archive = BytesIO()
    with ZipFile(archive, 'w') as zip_archive:
        # Walk once to find and exclude any python virtual envs
        for (dirpath, dirnames, filenames) in os.walk(root, onerror=handle_error):
            for name in filenames:
                full_name = os.path.join(dirpath, name)
                if 'pyvenv.cfg' in full_name:
                    exclude.append(os.path.relpath(os.path.dirname(full_name)))

        # Walk again to grab everything that's not excluded
        for (dirpath, dirnames, filenames) in os.walk(root, onerror=handle_error):
            dirnames[:] = [d for d in dirnames if not d.startswith(tuple(exclude))]

            for name in filenames:
                if name.endswith('.pyc'):
                    continue
                full_name = pathlib.Path(dirpath) / name
                fileinfo = ZipInfo(str(full_name.relative_to(rootpath)))
                with open(full_name, 'rb') as f:
                    zip_archive.writestr(fileinfo, f.read(), ZIP_DEFLATED)

    return archive.getbuffer()

@click.command()
@click.pass_context
@click.argument('runnable', required=True, type=click.Path(exists=True))
@click.option('--gateway', required=False, help='ID of gateway to which DUT is connected')
@click.option('--image', default='lagerdata/gatewaypy3', help='Docker image to use for running script')
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
        post_data.append(('module', zip_dir(runnable)))

    resp = session.run_python(gateway, files=post_data)
    kill_python = functools.partial(session.kill_python, gateway)
    stream_python_output(resp, kill_python)
