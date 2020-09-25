"""
    lager.wifi.commands

    Commands for controlling the wifi network
"""

import sys
import math
import click
from ..context import get_default_gateway
from ..status import run_job_output
from ..config import read_config_file

import click
from ..context import get_default_gateway


@click.group(name='wifi')
def _wifi():
    """
        Lager wifi commands
    """
    pass


@_wifi.command()
@click.pass_context
@click.option('--gateway', required=False, help='ID of gateway to which DUT is connected')
@click.option('--ssid', required=True, help='SSID of the network to connect to')
@click.option('--password', required=False, help='Password of the network to connect to', default='')
def connect(ctx, gateway, ssid, password=''):
    """
        Connect the gateway to a new network
    """
    if gateway is None:
        gateway = get_default_gateway(ctx)

    session = ctx.obj.session
    resp = session.connect_wifi(gateway, ssid, password)
    click.echo(resp.content, nl=False)
