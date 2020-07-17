"""
    lager.gdbserver.commands

    GDB Server tunnel commands
"""

import click
import trio
from .tunnel import serve_tunnel
from ..context import get_default_gateway, ensure_debugger_running

@click.command()
@click.pass_context
@click.option('--gateway', required=False, help='ID of gateway to which DUT is connected')
@click.option('--host', default='localhost', help='interface for gdbserver to bind. '
              'Use --host \'*\' to bind to all interfaces.', show_default=True)
@click.option('--port', default=3333, help='Port for gdbserver', show_default=True)
def gdbserver(ctx, gateway, host, port):
    """
        Establish a proxy to GDB server on gateway. By default binds to localhost, meaning gdb
        client connections must originate from the machine running `lager gdbserver`. If you would
        like to bind to all interfaces, use --host '*'
    """
    if gateway is None:
        gateway = get_default_gateway(ctx)

    ensure_debugger_running(gateway, ctx)

    connection_params = ctx.obj.websocket_connection_params(socktype='gdb-tunnel', gateway_id=gateway)
    try:
        trio.run(serve_tunnel, host, port, connection_params)
    except PermissionError as exc:
        if port < 1024:
            click.secho(f'Permission denied for port {port}. Using a port number less than '
                        '1024 typically requires root privileges.', fg='red', err=True)
        else:
            click.secho(str(exc), fg='red', err=True)
        if ctx.obj.debug:
            raise
    except OSError as exc:
        click.secho(f'Could not start gdbserver on port {port}: {exc}', fg='red', err=True)
        if ctx.obj.debug:
            raise
