"""
    lager_cli.util

    Catchall for utility functions
"""
import sys
import functools
import signal
import click
import trio
import lager_trio_websocket as trio_websocket
import wsproto.frame_protocol as wsframeproto
from .matchers import PythonMatcherV1

_FAILED_TO_RETRIEVE_EXIT_CODE = -1
_SIGTERM_EXIT_CODE = 124
_SIGKILL_EXIT_CODE = 137

def stream_output(response, chunk_size=1):
    """
        Stream an http response to stdout
    """
    for chunk in response.iter_content(chunk_size=chunk_size):
        click.echo(chunk, nl=False)
        sys.stdout.flush()

_ORIGINAL_SIGINT_HANDLER = signal.getsignal(signal.SIGINT)

def sigint_handler(kill_python, sig, frame):
    signal.signal(signal.SIGINT, _ORIGINAL_SIGINT_HANDLER)
    kill_python(signal.SIGINT)

def _stream_python_output_v1(response, kill_python, chunk_size):
    if 'Lager-Separator' not in response.headers:
        separator = None
    else:
        separator = response.headers['Lager-Separator'].encode()
    matcher = PythonMatcherV1(separator)
    handler = functools.partial(sigint_handler, kill_python)
    signal.signal(signal.SIGINT, handler)
    for chunk in response.iter_content(chunk_size=chunk_size):
        matcher.feed(chunk)
    exit_code = matcher.exit_code
    if exit_code == _FAILED_TO_RETRIEVE_EXIT_CODE:
        click.secho('Failed to retrieve script exit code.', fg='red', err=True)
    elif exit_code == _SIGTERM_EXIT_CODE:
        click.secho('Gateway script terminated due to timeout.', fg='red', err=True)
    elif exit_code == _SIGKILL_EXIT_CODE:
        click.secho('Gateway script forcibly killed due to timeout.', fg='red', err=True)
    sys.exit(matcher.exit_code)

def stream_python_output(response, kill_python, chunk_size=1):
    if response.headers.get('Lager-Output-Version') == '1':
        _stream_python_output_v1(response, kill_python, chunk_size)
    else:
        click.secho('Response format not supported. Please upgrade lager-cli', fg='red', err=True)
        sys.exit(1)

async def heartbeat(websocket, timeout, interval):
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
                await websocket.ping()
            await trio.sleep(interval)
    except trio_websocket.ConnectionClosed as exc:
        if exc.reason is None:
            return
        if exc.reason.code != wsframeproto.CloseReason.NORMAL_CLOSURE or exc.reason.reason != 'EOF':
            raise
