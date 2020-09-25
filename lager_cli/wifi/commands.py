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
@click.option('--gateway', required=False, help='ID of gateway')
def status(ctx, gateway):
    """
        Get the current WiFi Status of the gateway
    """
    if gateway is None:
        gateway = get_default_gateway(ctx)

    session = ctx.obj.session
    resp = session.get_wifi_state(gateway)
    resp.raise_for_status()


    click.echo(resp.content, nl=False)


@_wifi.command()
@click.pass_context
@click.option('--gateway', required=False, help='ID of gateway')
def access_points(ctx, gateway):
    """
        Get WiFi access points visible to the gateway
    """
    if gateway is None:
        gateway = get_default_gateway(ctx)

    session = ctx.obj.session
    resp = session.get_wifi_access_points(gateway)
    resp.raise_for_status()
    click.echo(resp.content, nl=False)


@_wifi.command()
@click.pass_context
@click.option('--gateway', required=False, help='ID of gateway')
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
    resp.raise_for_status()


@_wifi.command()
@click.pass_context
@click.option('--gateway', required=False, help='ID of gateway')
@click.option('--ssid', required=True, help='SSID of the network to delete')
def delete_connection(ctx, gateway, ssid):
    """
        Delete the specified network from the gateway
    """
    if gateway is None:
        gateway = get_default_gateway(ctx)

    session = ctx.obj.session
    resp = session.delete_wifi_connection(gateway, ssid)
    click.echo(resp.content, nl=False)
    resp.raise_for_status()
