"""
    lager.paramtypes

    Custom click paramtypes
"""
import collections
import os
import re
import click

class MemoryAddressType(click.ParamType):
    """
        Memory address integer parameter
    """
    name = 'memory address'

    def convert(self, value, param, ctx):
        """
            Parse string reprsentation of a hex integer
        """
        value = value.strip().lower()
        if value.lower().startswith('0x'):
            try:
                return int(value, 16)
            except ValueError:
                self.fail(f"{value} is not a valid hex integer", param, ctx)

        try:
            return int(value, 10)
        except ValueError:
            self.fail(f"{value} is not a valid integer", param, ctx)

    def __repr__(self):
        return 'ADDR'

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

class VarAssignmentType(click.ParamType):
    """
        Openocd variable parameter
    """
    name = 'FOO=BAR'

    def convert(self, value, param, ctx):
        """
            Parse a variable assignment
        """
        parts = value.split('=')
        if len(parts) != 2:
            self.fail('Invalid assignment', param, ctx)

        return parts

    def __repr__(self):
        return 'VAR ASSIGNMENT'

class EnvVarType(click.ParamType):
    """
        Environment variable
    """
    name = 'FOO=BAR'
    regex = re.compile(r'\A[a-zA-Z_]{1,}[a-zA-Z0-9_]{0,}\Z')

    def convert(self, value, param, ctx):
        """
            Parse string representation of environment variable
        """
        parts = value.split('=', maxsplit=1)
        if len(parts) != 2:
            self.fail('Invalid assignment', param, ctx)

        name = parts[0]
        if not self.regex.match(name):
            self.fail(f'Invalid environment variable name "{name}". Names must begin with a letter or underscore, and may only contain letters, underscores, and digits', param, ctx)

        return value

    def __repr__(self):
        return 'ENV VAR'

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
