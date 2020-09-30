"""
    lager_cli.util

    Catchall for utility functions
"""
import sys
import math
import pathlib
import os
import functools
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED
from io import BytesIO
import signal
import click
import trio
import lager_trio_websocket as trio_websocket
import wsproto.frame_protocol as wsframeproto
from .matchers import iter_streams

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

STDOUT_FILENO = 1
STDERR_FILENO = 2

def sigint_handler(kill_python, _sig, _frame):
    """
        Handle Ctrl+C by restoring the old signal handler (so that subsequent Ctrl+C will actually
        stop python), and send the SIGTERM to the running docker container.
    """
    click.echo(' Attempting to stop Lager Python job')
    signal.signal(signal.SIGINT, _ORIGINAL_SIGINT_HANDLER)
    kill_python(signal.SIGINT)

def _do_exit(exit_code):
    if exit_code == _FAILED_TO_RETRIEVE_EXIT_CODE:
        click.secho('Failed to retrieve script exit code.', fg='red', err=True)
    elif exit_code == _SIGTERM_EXIT_CODE:
        click.secho('Gateway script terminated due to timeout.', fg='red', err=True)
    elif exit_code == _SIGKILL_EXIT_CODE:
        click.secho('Gateway script forcibly killed due to timeout.', fg='red', err=True)
    sys.exit(exit_code)

def _echo_stdout(chunk):
    click.echo(chunk, nl=False)
    sys.stdout.flush()

def _echo_stderr(chunk):
    click.echo(chunk, err=True, nl=False)
    sys.stderr.flush()

def _stream_python_output_v1(response, kill_python, stdout_handler=None, stderr_handler=None):
    handler = functools.partial(sigint_handler, kill_python)
    signal.signal(signal.SIGINT, handler)
    sys.stdout.flush()
    for (fileno, chunk) in iter_streams(response):
        if fileno == -1:
            exit_code = int(chunk.decode(), 10)
            _do_exit(exit_code)
        else:
            if fileno == STDOUT_FILENO and stdout_handler:
                stdout_handler(chunk)
            elif fileno == STDERR_FILENO and stderr_handler:
                stderr_handler(chunk)

def stream_python_output(response, kill_python):
    version = response.headers.get('Lager-Output-Version')
    if version == '1':
        _stream_python_output_v1(response, kill_python, _echo_stdout, _echo_stderr)
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


def handle_error(error):
    """
        os.walk error handler, just raise it
    """
    raise error

class SizeLimitExceeded(RuntimeError):
    """
        Raised if zip file size limit exceeded
    """


def zip_dir(root, max_content_size=math.inf):
    """
        Zip a directory into memory
    """
    rootpath = pathlib.Path(root)
    exclude = ['.git']
    archive = BytesIO()
    total_size = 0
    with ZipFile(archive, 'w') as zip_archive:
        # Walk once to find and exclude any python virtual envs
        for (dirpath, dirnames, filenames) in os.walk(root, onerror=handle_error):
            for name in filenames:
                full_name = os.path.join(dirpath, name)
                if 'pyvenv.cfg' in full_name:
                    exclude.append(os.path.relpath(os.path.dirname(full_name)))

        # Walk again to grab everything that's not excluded
        for (dirpath, dirnames, filenames) in os.walk(root, onerror=handle_error):
            dirnames[:] = [d for d in dirnames if not d.startswith(tuple(exclude))]

            for name in filenames:
                if name.endswith('.pyc'):
                    continue
                full_name = pathlib.Path(dirpath) / name
                total_size += os.path.getsize(full_name)
                if total_size > max_content_size:
                    raise SizeLimitExceeded

                fileinfo = ZipInfo(str(full_name.relative_to(rootpath)))
                with open(full_name, 'rb') as f:
                    zip_archive.writestr(fileinfo, f.read(), ZIP_DEFLATED)
    return archive.getbuffer()
