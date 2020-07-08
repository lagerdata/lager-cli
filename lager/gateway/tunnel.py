"""
    lager.gateway.tunnel

    GDB tunnel functions
"""
import functools
import logging
import click
import trio
import trio_websocket
from ..context import get_ssl_context

logger = logging.getLogger(__name__)

async def send_to_websocket(websocket, gdb_client_stream, nursery):
    """
        Read data from gdb_client_stream (a trio stream connected to a gdb client)
        and send to websocket (ultimate destination is gateway gdbserver).
    """
    try:
        async with gdb_client_stream:
            async for msg in gdb_client_stream:
                await websocket.send_message(msg)
    finally:
        nursery.cancel_scope.cancel()


async def send_to_gdb(websocket, gdb_client_stream, nursery):
    """
        Read data from websocket (originating from gateway gdbserver)
        and send to gdb_client_stream (a trio stream connected to a gdb client)
    """
    while True:
        try:
            msg = await websocket.get_message()
            await gdb_client_stream.send_all(msg)
        except trio_websocket.ConnectionClosed:
            nursery.cancel_scope.cancel()

async def connection_handler(connection_params, gdb_client_stream):
    """
        Handle a single connection from a gdb client
    """
    (uri, kwargs) = connection_params
    sockname = gdb_client_stream.socket.getsockname()
    click.echo(f'Serving gdb client: {sockname}')
    try:
        ctx = get_ssl_context()
        async with trio_websocket.open_websocket_url(uri, ssl_context=ctx, disconnect_timeout=1, **kwargs) as websocket:
            async with trio.open_nursery() as nursery:
                nursery.start_soon(send_to_websocket, websocket, gdb_client_stream, nursery)
                nursery.start_soon(send_to_gdb, websocket, gdb_client_stream, nursery)
    except Exception as exc:  # pylint: disable=broad-except
        logger.exception('Exception in connection_handler', exc_info=exc)
    finally:
        click.echo(f'gdb client disconnected: {sockname}')



async def serve_tunnel(host, port, connection_params, *, task_status=trio.TASK_STATUS_IGNORED):
    """
        Start up the server that tunnels traffic to a gdbserver instance running on a gateway
    """
    # (uri, kwargs) = connection_params
    async with trio.open_nursery() as nursery:
        handler = functools.partial(connection_handler, connection_params)
        serve_listeners = functools.partial(trio.serve_tcp, handler, port, host=host)

        server = await nursery.start(serve_listeners)
        task_status.started(server)
        click.echo(f'Serving GDB on {host}:{port}. Press Ctrl+C to quit.')
        try:
            await trio.sleep_forever()
        except KeyboardInterrupt:
            nursery.cancel_scope.cancel()
