"""
    lager.status

    Job status output functions
"""
from functools import partial
import bson
import click
import trio
import trio_websocket
from trio_websocket import open_websocket_url
import wsproto.frame_protocol as wsframeproto
import requests

def stream_response(response):
    """
        Stream a ``requests`` response to the terminal
    """
    with response:
        for chunk in response.iter_content(chunk_size=None):
            click.echo(chunk, nl=False)

async def handle_url_message(urls):
    """
        Handle a message with data location urls
    """
    downloader = partial(requests.get, stream=True)
    for url in urls:
        response = await trio.to_thread.run_sync(downloader, url)
        response.raise_for_status()
        await trio.to_thread.run_sync(stream_response, response)

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

class InterMessageTimeout(Exception):
    """
        Raised if no messages received for ``message_timeout`` seconds
    """
    pass

async def display_job_output(connection_params, message_timeout, overall_timeout):
    """
        Display job output from websocket
    """
    (uri, kwargs) = connection_params
    with trio.fail_after(overall_timeout):
        async with open_websocket_url(uri, disconnect_timeout=1, **kwargs) as websocket:
            while True:
                try:
                    with trio.fail_after(message_timeout):
                        message = await websocket.get_message()
                except trio.TooSlowError:
                    raise InterMessageTimeout(message_timeout)
                await handle_message(bson.loads(message))

def run_job_output(connection_params, message_timeout, overall_timeout, debug=False):
    """
        Run async task to get job output from websocket
    """
    try:
        trio.run(display_job_output, connection_params, message_timeout, overall_timeout)
    except trio.TooSlowError:
        suffix = '' if overall_timeout == 1 else 's'
        message = f'Job status timed out after {overall_timeout} second{suffix}'
        click.secho(message, fg='red', err=True)
        click.get_current_context().exit(1)
    except InterMessageTimeout:
        suffix = '' if message_timeout == 1 else 's'
        message = f'Timed out after no messages received for {message_timeout} second{suffix}'
        click.secho(message, fg='red', err=True)
        click.get_current_context().exit(1)
    except requests.exceptions.HTTPError as exc:
        response = getattr(exc, 'response')
        if response is not None and response.status_code == 404:
            click.secho('Test run content not found', fg='red', err=True)
        else:
            click.secho('Error retrieving test run content', fg='red', err=True)
        if debug:
            raise
    except trio_websocket.HandshakeError as exc:
        if exc.status_code == 404:
            click.secho('Job not found', fg='red', err=True)
        else:
            click.secho('Could not connect to API websocket', fg='red', err=True)
        if debug:
            raise
        click.get_current_context().exit(1)
    except trio_websocket.ConnectionClosed as exc:
        if exc.reason.code != wsframeproto.CloseReason.NORMAL_CLOSURE:
            click.secho('API websocket closed abnormally', fg='red', err=True)
            if debug:
                raise
            click.get_current_context().exit(1)
        elif exc.reason.reason != 'EOF':
            click.secho('API websocket closed unexpectedly', fg='red', err=True)
            if debug:
                raise
            click.get_current_context().exit(1)
    except ConnectionRefusedError:
        click.secho('Lager API websocket connection refused!', fg='red', err=True)
        if debug:
            raise
        click.get_current_context().exit(1)
    except trio_websocket.ConnectionRejected as exc:
        if exc.status_code == 404:
            click.secho('Job not found', fg='red', err=True)
        elif exc.status_code >= 500:
            click.secho('Internal error in Lager API. '
                        'Please contact support@lagerdata.com if this persists.',
                        fg='red', err=True)
        if debug:
            raise
        click.get_current_context().exit(1)
