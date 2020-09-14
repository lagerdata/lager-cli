"""
    conftest.py
"""
import sys
import os
import contextlib
import functools
import trio
import lager_trio_websocket
import requests_mock
import bson
import pytest

# A bit of a hack, but let's add the current directory where this conftest
# is to sys.path, so that we can run `pytest` directly here without having
# to make the current project editable (`pip install -e`) or without having
# to invoke it with `python -m pytest` (which effectively does the sys.path add).

#pylint: disable=invalid-name,unused-argument,redefined-outer-name
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

@pytest.fixture
def make_server():
    """
        Return an async context manager that can be used to start a server with a
        given handler coroutine function
    """
    @contextlib.asynccontextmanager
    async def server_fn(handler):
        async with trio.open_nursery() as nursery:
            server_fn = functools.partial(lager_trio_websocket.serve_websocket, handler, 'localhost', 0, ssl_context=None)
            server = await nursery.start(server_fn)
            for listener in server.listeners:
                if '::' not in listener.url:
                    yield listener.url
            nursery.cancel_scope.cancel()

    return server_fn

@pytest.fixture
def streaming_data():
    """
        Example streamed data
    """
    return [
        {
            'entry': {'payload': b'foo'},
        },
        {
            'entry': {'payload': b'bar'},
        },
        {
            'entry': {'payload': b'baz\n'},
        },
    ]

@pytest.fixture
def data_server(streaming_data):
    """
        Returns a coroutine function that is a websocket handler for serving
        `streaming_data`
    """
    async def handler_fn(request):
        websocket = await request.accept()
        message = bson.dumps({
            'data': streaming_data,
        })
        await websocket.send_message(message)
        await websocket.aclose(reason='EOF')
    return handler_fn

@pytest.fixture
def mock_response_content():
    return 'response'

@pytest.fixture
def download_urls(mock_response_content):
    urls = [
        'https://example.com',
        'https://example.com/foo',
    ]
    with requests_mock.Mocker() as m:
        for url in urls:
            m.get(url, text=mock_response_content)
        yield urls

@pytest.fixture
def download_server(download_urls):
    """
        Returns a coroutine function that is a websocket handler for serving
        `urls`
    """
    async def handler_fn(request):
        websocket = await request.accept()
        message = bson.dumps({
            'urls': download_urls,
        })
        await websocket.send_message(message)
        await websocket.aclose(reason='EOF')
    return handler_fn
