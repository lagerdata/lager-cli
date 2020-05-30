"""
    lager.status

    Job status output functions
"""
import asyncio
import bson
import click
import websockets

async def display_job_output(connection_params):
    """
        Display job output from websocket
    """
    (uri, kwargs) = connection_params
    try:
        async with websockets.connect(uri, close_timeout=1, **kwargs) as websocket:
            try:
                async for message in websocket:
                    parsed_message = bson.loads(message)['data']
                    for item in parsed_message:
                        entry = item['entry']
                        if 'payload' in entry:
                            click.echo(entry['payload'].decode(), nl=False)
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
