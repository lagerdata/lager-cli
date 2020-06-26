"""
    lager.flash.commands

    Commands for flashing a DUT
"""
import os
import collections
import itertools
import click
from ..context import get_default_gateway

class HexParamType(click.ParamType):
    """
        Hexadecimal integer parameter
    """
    name = 'hex'

    def convert(self, value, param, ctx):
        """
            Parse string reprsentation of a hex integer
        """
        try:
            return int(value, 16)
        except ValueError:
            self.fail(f"{value} is not a valid hex integer", param, ctx)

    def __repr__(self):
        return 'HEX'

Binfile = collections.namedtuple('Binfile', ['path', 'address'])
class BinfileType(click.ParamType):
    """
        Type to represent a command line argument for a binfile (<path>,<address>)
    """
    envvar_list_splitter = os.path.pathsep
    name = 'binfile'

    def __init__(self, *args, exists=False, **kwargs):
        self.exists = exists
        super().__init__(*args, **kwargs)

    def convert(self, value, param, ctx):
        """
            Convert binfile param string into useable components
        """
        parts = value.rsplit(',', 1)
        if len(parts) != 2:
            self.fail(f'{value}. Syntax: --binfile <filename>,<address>', param, ctx)
        filename, address = parts
        path = click.Path(exists=self.exists).convert(filename, param, ctx)
        address = HexParamType().convert(address, param, ctx)

        return Binfile(path=path, address=address)

    def __repr__(self):
        return 'BINFILE'

@click.command()
@click.pass_context
@click.option('--gateway', required=False, help='ID of gateway to which DUT is connected')
@click.option(
    '--hexfile',
    multiple=True, type=click.Path(exists=True),
    help='Hexfile(s) to flash. May be passed multiple times; files will be flashed in order.')
@click.option(
    '--binfile',
    multiple=True, type=BinfileType(exists=True),
    help='Binfile(s) to flash. Syntax: --binfile `<filename>,<address>` '
         'May be passed multiple times; files will be flashed in order.')
@click.option(
    '--preverify/--no-preverify',
    help='If true, only flash target if image differs from current flash contents',
    default=True)
@click.option('--verify/--no-verify', help='Verify image successfully flashed', default=True)
@click.option('--force', is_flag=True)
def flash(ctx, gateway, hexfile, binfile, preverify, verify, force):
    """
        Flash gateway
    """
    if gateway is None:
        gateway = get_default_gateway(ctx)

    session = ctx.obj.session
    url = 'gateway/{}/flash-duck'.format(gateway)
    files = list(zip(itertools.repeat('hexfile'), [open(path, 'rb') for path in hexfile]))
    files.extend(
        zip(itertools.repeat('binfile'), [open(binf.path, 'rb') for binf in binfile])
    )
    files.extend(
        zip(itertools.repeat('binfile_address'), [binf.address for binf in binfile])
    )
    files.append(('preverify', preverify))
    files.append(('verify', verify))
    files.append(('force', force))

    resp = session.post(url, files=files, stream=True)
    for chunk in resp.iter_content(chunk_size=8):
        click.echo(chunk, nl=False)
