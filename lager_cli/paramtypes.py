"""
    lager.paramtypes

    Custom click paramtypes
"""
import collections
import os
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
        Hexadecimal integer parameter
    """
    name = 'FOO=BAR'

    def convert(self, value, param, ctx):
        """
            Parse string reprsentation of a hex integer
        """
        parts = value.split('=')
        if len(parts) != 2:
            raise ValueError('Invalid assignment')

        return parts

    def __repr__(self):
        return 'VAR ASSIGNMENT'

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
