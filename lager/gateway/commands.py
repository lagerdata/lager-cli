"""
    lager.gateway.commands

    Gateway commands
"""
import os
import itertools
import requests
import urllib3
import click

_DEFAULT_HOST = 'https://lagerdata.com'

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
    host = os.getenv('LAGER_HOST', _DEFAULT_HOST)
    verify = 'NOVERIFY' not in os.environ
    if not verify:
        urllib3.disable_warnings()

    url = '{}/api/v1/gateway/{}/flash-duck'.format(host, name)
    auth = ctx.obj
    headers = {
        'Authorization': '{} {}'.format(auth['type'], auth['token'])
    }
    files = zip(itertools.repeat('hexfile'), [open(path) for path in hexfile])
    resp = requests.post(url, files=files, headers=headers, verify=verify, stream=True)
    resp.raise_for_status()
    for chunk in resp.iter_content(chunk_size=None):
        print(chunk.decode(), end='', flush=True)
