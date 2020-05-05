"""
    lager.gateway.commands

    Gateway commands
"""
import click
from lager.config import read_config_file, write_config_file

@click.group(name='set')
def setter():
    """
        Lager setter commands
    """
    pass

@setter.group()
def default():
    """
        Set defaults
    """
    pass

@default.command()
@click.argument('gateway_id')
def gateway(gateway_id):
    """
        Set default gateway
    """
    config = read_config_file()
    if 'LAGER' not in config:
        config.add_section('LAGER')

    config.set('LAGER', 'gateway_id', gateway_id)
    write_config_file(config)
