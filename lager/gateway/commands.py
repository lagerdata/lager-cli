"""
    lager.gateway.commands

    Gateway commands
"""
import os
import itertools
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
@click.option('--hexfile', multiple=True, required=True, type=click.Path(exists=True))
def flash(ctx, name, hexfile):
    """
        Flash gateway
    """
    url = '{}/api/v1/gateway/{}/flash-duck'.format(HOST, name)
    auth = ctx.obj
    headers = {
        'Authorization': '{} {}'.format(auth['type'], auth['token'])
    }
    files = zip(itertools.repeat('hexfile'), [open(path) for path in hexfile])
    resp = requests.post(url, files=files, headers=headers, verify=False)
    resp.raise_for_status()
    print(resp.content)
