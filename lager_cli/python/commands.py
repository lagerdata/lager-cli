"""
    lager.flash.commands

    Commands for flashing a DUT
"""
import os
import itertools
from zipfile import ZipFile, ZipInfo
from io import BytesIO
import base64
import click
from ..context import get_default_gateway
from ..util import stream_python_output
from ..paramtypes import EnvVarType

def handle_error(error):
    raise error

def zip_dir(root):
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
                full_name = os.path.join(dirpath, name)
                relative_name = os.path.basename(full_name)
                fileinfo = ZipInfo(relative_name)
                with open(full_name, 'rb') as f:
                    zip_archive.writestr(fileinfo, f.read())

    return archive.getbuffer()

@click.command()
@click.pass_context
@click.argument('runnable', required=True, type=click.Path(exists=True))
@click.option('--gateway', required=False, help='ID of gateway to which DUT is connected')
@click.option('--image', default='lagerdata/gatewaypy3', help='Docker image to use for running script')
@click.option(
    '--env',
    multiple=True, type=EnvVarType(), help='Environment variables')
@click.option(
    '--file', 'files',
    multiple=True, type=click.Path(exists=True, dir_okay=False), help='Files which will be made available to your script')
@click.option('--kill', is_flag=True, default=False)
@click.option('--timeout', type=click.INT, required=False)
def python(ctx, runnable, gateway, image, env, files, kill, timeout):
    """
        Run a python script on the gateway
    """
    session = ctx.obj.session
    if gateway is None:
        gateway = get_default_gateway(ctx)

    if kill:
        resp = session.kill_python(gateway).json()
        click.echo(base64.b64decode(resp['stderr']), err=True, nl=False)
        return

    post_data = [
        ('image', image),
    ]
    post_data.extend(
        zip(itertools.repeat('env'), env)
    )
    post_data.extend(
        zip(itertools.repeat('filename'), files)
    )
    post_data.extend(
        zip(itertools.repeat('file'), [open(filename, 'rb') for filename in files])
    )
    if timeout is not None:
        post_data.append(('timeout', timeout))

    if os.path.isfile(runnable):
        with open(runnable, 'r') as script_file:
            post_data.append(('script', script_file.read()))
    elif os.path.isdir(runnable):
        post_data.append(('module', zip_dir(runnable)))

    resp = session.run_python(gateway, files=post_data)
    stream_python_output(resp)
