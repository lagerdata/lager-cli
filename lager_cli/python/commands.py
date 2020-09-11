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
from ..util import stream_output
from ..paramtypes import EnvVarType

def handle_error(error):
    raise error

def zip_dir(root):
    archive = BytesIO()
    with ZipFile(archive, 'w') as zip_archive:
        for (dirpath, dirnames, filenames) in os.walk(root, onerror=handle_error):
            for name in filenames:
                if name.endswith('.pyc'):
                    continue
                full_name = os.path.join(dirpath, name)
                relative_name = full_name.split(root)[1][1:]
                fileinfo = ZipInfo(relative_name)
                with open(full_name, 'rb') as f:
                    zip_archive.writestr(fileinfo, f.read())

    return archive.getbuffer()

@click.command()
@click.pass_context
@click.argument('script', required=False, type=click.File('rb'))
@click.option('--gateway', required=False, help='ID of gateway to which DUT is connected')
@click.option('--image', default='lagerdata/gatewaypy3', help='Docker image to use for running script')
@click.option('--module', required=False, help='Python module to run', type=click.Path(exists=True, file_okay=False, resolve_path=True))
@click.option(
    '--env',
    multiple=True, type=EnvVarType(), help='Environment variables')
def python(ctx, script, gateway, image, module, env):
    """
        Run a python script on the gateway
    """
    if gateway is None:
        gateway = get_default_gateway(ctx)

    if not script and not module:
        click.echo('Error: script or module not provided', err=True)
        ctx.exit(1)

    files = [
        ('image', image),
    ]
    files.extend(
        zip(itertools.repeat('env'), env)
    )

    if module:
        files.append(('module', zip_dir(module)))

    if script:
        files.append(('script', script.read()))

    session = ctx.obj.session
    resp = session.run_python(gateway, files=files)
    output = resp.json()
    output['stdout'] = base64.b64decode(output['stdout'])
    output['stderr'] = base64.b64decode(output['stderr'])
    click.echo(output['stdout'], nl=False)
    click.echo(output['stderr'], nl=False, err=True)
    ctx.exit(output['returncode'])
