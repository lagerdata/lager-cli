"""
    lager.gateway.commands

    Gateway commands
"""
import os
import requests
import click

_DEFAULT_HOST = 'https://lagerdata.com'
HOST = os.getenv('LAGER_HOST', _DEFAULT_HOST)

@click.group()
def gateway():
    """
        Lager gateway commands
    """
    pass

@gateway.command()
@click.pass_context
@click.argument('name')
@click.argument('hexfile')
def flash(ctx, name, hexfile):
    """
        Flash gateway
    """
    try:
        hexfile = open(hexfile)
    except FileNotFoundError:
        click.secho('{} not found!'.format(hexfile), err=True, fg='red')
        ctx.exit()
    url = '{}/api/v1/gateway/{}/flash-duck'.format(HOST, name)
    auth = ctx.obj
    headers = {
        'Authorization': '{} {}'.format(auth['type'], auth['token'])
    }
    files = {
        'hexfile': hexfile,
    }
    resp = requests.post(url, files=files, headers=headers, verify=False)
    resp.raise_for_status()
    print(resp.json())
