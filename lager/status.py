"""
    lager.status

    Job status output functions
"""
import asyncio
import bson
import click
import websockets
import requests

async def handle_url_message(urls):
    """
        Handle a message with data location urls
    """
    loop = asyncio.get_running_loop()
    for url in urls:
        response = await loop.run_in_executor(None, requests.get, url)
        click.echo(response.content.decode(), nl=False)

async def handle_data_message(message):
    """
        Handle a data message
    """
    for item in message:
        entry = item['entry']
        if 'payload' in entry:
            click.echo(entry['payload'].decode(), nl=False)

async def handle_message(message):
    """
        Handle an individual parsed websocket message
    """
    if 'data' in message:
        return await handle_data_message(message['data'])
    if 'urls' in message:
        return await handle_url_message(message['urls'])
    return None

async def display_job_output(connection_params):
    """
        Display job output from websocket
    """
    (uri, kwargs) = connection_params
    try:
        async with websockets.connect(uri, close_timeout=1, **kwargs) as websocket:
            try:
                async for message in websocket:
                    await handle_message(bson.loads(message))
            except Exception as e:
                for task in asyncio.all_tasks():
                    task.cancel()
                raise
    except:
        for task in asyncio.all_tasks():
            task.cancel()
        raise

def run_job_output(connection_params):
    """
        Run async task to get job output from websocket
    """
    try:
        asyncio.run(display_job_output(connection_params), debug=True)
    except asyncio.CancelledError:
        click.secho('Unexpected disconect from Lager API!', fg='red', err=True)
    except ConnectionRefusedError:
        click.secho('Could not connect to Lager API!', fg='red', err=True)
        click.get_current_context().exit(1)
    except websockets.exceptions.InvalidStatusCode as exc:
        if exc.status_code == 404:
            click.secho('Job not found', fg='red', err=True)
            click.get_current_context().exit(1)
        elif exc.status_code >= 500:
            click.secho('Internal error in Lager API. '
                        'Please contact support@lagerdata.com if this persists.',
                        fg='red', err=True)
            click.get_current_context().exit(1)
        raise
