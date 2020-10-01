"""
    lager_cli.util

    Catchall for utility functions
"""
import sys
import math
import pathlib
import os
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED
from io import BytesIO
import click
import trio
import lager_trio_websocket as trio_websocket
import wsproto.frame_protocol as wsframeproto
from .matchers import iter_streams
from .safe_unpickle import restricted_loads
from .exceptions import OutputFormatNotSupported

FAILED_TO_RETRIEVE_EXIT_CODE = -1
SIGTERM_EXIT_CODE = 124
SIGKILL_EXIT_CODE = 137

def stream_output(response, chunk_size=1):
    """
        Stream an http response to stdout
    """
    for chunk in response.iter_content(chunk_size=chunk_size):
        click.echo(chunk, nl=False)
        sys.stdout.flush()

STDOUT_FILENO = 1
STDERR_FILENO = 2
OUTPUT_CHANNEL_FILENO = 3

def _echo_stdout(chunk):
    click.echo(chunk, nl=False)
    sys.stdout.flush()

def _echo_stderr(chunk):
    click.echo(chunk, err=True, nl=False)
    sys.stderr.flush()

def _output_handler(chunk):
    print(f'Got a chunk: {chunk}')

class OutputHandler:
    def __init__(self, object_callback):
        self.object_callback = object_callback
        self.len = None
        self.buffer = b''

    def parse(self):
        if self.len is None:
            parts = self.buffer.split(b' ', 1)
            if len(parts) == 1:
                return
            self.len = int(parts[0], 10)
            self.buffer = parts[1]
            return self.parse()

        if len(self.buffer) >= self.len:
            pickled = self.buffer[:self.len]
            self.buffer = self.buffer[self.len:]
            self.len = None
            obj = restricted_loads(pickled)
            self.object_callback(obj)
            return self.parse()

    def receive(self, chunk):
        self.buffer += chunk
        self.parse()


def stream_python_output_v1(response, stdout_handler=None, stderr_handler=None):
    output_handler = OutputHandler(click.echo)
    for (fileno, chunk) in iter_streams(response):
        if fileno == -1:
            return int(chunk.decode(), 10)

        if fileno == STDOUT_FILENO and stdout_handler:
            stdout_handler(chunk)
        elif fileno == STDERR_FILENO and stderr_handler:
            stderr_handler(chunk)
        elif fileno == OUTPUT_CHANNEL_FILENO:
            output_handler.receive(chunk)

def stream_python_output(response):
    version = response.headers.get('Lager-Output-Version')
    if version == '1':
        return stream_python_output_v1(response, _echo_stdout, _echo_stderr)
    raise OutputFormatNotSupported

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
