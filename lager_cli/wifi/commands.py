"""
    lager.wifi.commands

    Commands for controlling the wifi network
"""

import click
from texttable import Texttable

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

    click.echo('State: {}'.format(resp.json().get('state')))
    click.echo('SSID:  {}'.format(resp.json().get('ssid')))


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

    table = Texttable()
    table.set_deco(Texttable.HEADER)
    table.set_cols_dtype(['t', 't', 'i'])
    table.set_cols_align(['l', 'l', 'r'])
    table.header(['ssid', 'security', 'strength'])
    for ap in resp.json().get('access_points', []):
        table.add_row([ap['ssid'], ap['security'], ap['strength']])

    click.echo(table.draw())

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
    resp.raise_for_status()
    if resp.json().get('acknowledged'):
        click.echo('Acknowledged', nl=False)


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
    resp.raise_for_status()
    if resp.json().get('acknowledged'):
        click.echo('Acknowledged', nl=False)
