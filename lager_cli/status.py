"""
    lager.status

    Job status output functions
"""
import curses
import threading
import sys
from functools import partial
import bson
import click
import trio
import trio_websocket
from trio_websocket import open_websocket_url
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
import wsproto.frame_protocol as wsframeproto
import requests
from .matchers import test_matcher_factory

def stream_response(response):
    """
        Stream a ``requests`` response to the terminal
    """
    with response:
        for chunk in response.iter_content(chunk_size=None):
            click.echo(chunk, nl=False)

async def handle_url_message(matcher, urls):
    """
        Handle a message with data location urls
    """
    downloader = partial(requests.get, stream=True)
    for url in urls:
        response = await trio.to_thread.run_sync(downloader, url)
        response.raise_for_status()
        await trio.to_thread.run_sync(stream_response, response)

async def handle_data_message(matcher, message):
    """
        Handle a data message
    """
    for item in message:
        entry = item['entry']
        if 'payload' in entry:
            payload = entry['payload']
            matcher.feed(payload)

async def handle_message(matcher, message):
    """
        Handle an individual parsed websocket message
    """
    if 'data' in message:
        return await handle_data_message(matcher, message['data'])
    if 'urls' in message:
        return await handle_url_message(matcher, message['urls'])
    return None

class InterMessageTimeout(Exception):
    """
        Raised if no messages received for ``message_timeout`` seconds
    """
    pass

async def heartbeat(ws, timeout, interval):
    '''
    Send periodic pings on WebSocket ``ws``.

    Wait up to ``timeout`` seconds to send a ping and receive a pong. Raises
    ``TooSlowError`` if the timeout is exceeded. If a pong is received, then
    wait ``interval`` seconds before sending the next ping.

    This function runs until cancelled.

    :param ws: A WebSocket to send heartbeat pings on.
    :param float timeout: Timeout in seconds.
    :param float interval: Interval between receiving pong and sending next
        ping, in seconds.
    :raises: ``ConnectionClosed`` if ``ws`` is closed.
    :raises: ``TooSlowError`` if the timeout expires.
    :returns: This function runs until cancelled.
    '''
    try:
        while True:
            with trio.fail_after(timeout):
                await ws.ping()
            await trio.sleep(interval)
    except trio_websocket.ConnectionClosed as exc:
        if exc.reason is None:
            return
        if exc.reason.code != wsframeproto.CloseReason.NORMAL_CLOSURE or exc.reason.reason != 'EOF':
            raise

async def read_from_websocket(websocket, matcher, message_timeout, nursery):
    try:
        while True:
            try:
                with trio.fail_after(message_timeout):
                    try:
                        message = await websocket.get_message()
                    except trio_websocket.ConnectionClosed as exc:
                        if exc.reason is None:
                            return
                        if exc.reason.code != wsframeproto.CloseReason.NORMAL_CLOSURE or exc.reason.reason != 'EOF':
                            raise
                        break
            except trio.TooSlowError:
                raise InterMessageTimeout(message_timeout)
            await handle_message(matcher, bson.loads(message))
    finally:
        matcher.done()
        nursery.cancel_scope.cancel()

def thread_function(stdscr, send_channel, trio_token):
    while True:
        char = stdscr.getch()
        if char == -1:
            trio.from_thread.run(send_channel.send, {'type': 'EOF'}, trio_token=trio_token)
            break
        elif char <= 255:
            trio.from_thread.run(send_channel.send, {'type': 'key', 'value': char}, trio_token=trio_token)
        else:
            print(char)


async def write_to_websocket(websocket, receive_channel, nursery):
    try:
        while True:
            message = await receive_channel.receive()
            if message['type'] == 'EOF':
                await websocket.aclose()
                return

            if message['type'] == 'key':
                value = message['value']
                try:
                    await websocket.send_message(bytes([value]))
                except trio_websocket.ConnectionClosed as exc:
                    if exc.reason is None:
                        return
                    if exc.reason.code != wsframeproto.CloseReason.NORMAL_CLOSURE or exc.reason.reason != 'EOF':
                        raise
                    return
    finally:
        nursery.cancel_scope.cancel()

@retry(reraise=True, sleep=trio.sleep, stop=stop_after_attempt(4), wait=wait_fixed(2), retry=retry_if_exception_type(trio_websocket.ConnectionRejected))
async def display_job_output(connection_params, test_runner, message_timeout, overall_timeout):
    """
        Display job output from websocket
    """
    (uri, kwargs) = connection_params
    match_class = test_matcher_factory(test_runner)
    try:
        stdscr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        stdscr.keypad(True)
        matcher = match_class(stdscr)
        send_channel, receive_channel = trio.open_memory_channel(0)
        with trio.fail_after(overall_timeout):
            async with open_websocket_url(uri, disconnect_timeout=1, **kwargs) as websocket:
                token = trio.lowlevel.current_trio_token()
                thread = threading.Thread(target=thread_function, args=(stdscr, send_channel, token), daemon=True)
                thread.start()
                async with trio.open_nursery() as nursery:
                    nursery.start_soon(heartbeat, websocket, 30, 30)
                    nursery.start_soon(read_from_websocket, websocket, matcher, message_timeout, nursery)
                    nursery.start_soon(write_to_websocket, websocket, receive_channel, nursery)
        return matcher
    finally:
        curses.nocbreak()
        stdscr.keypad(False)
        curses.echo()
        curses.endwin()

def run_job_output(connection_params, test_runner, message_timeout, overall_timeout, debug=False):
    """
        Run async task to get job output from websocket
    """
    try:
        matcher = trio.run(display_job_output, connection_params, test_runner, message_timeout, overall_timeout)
        click.get_current_context().exit(matcher.exit_code)
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
