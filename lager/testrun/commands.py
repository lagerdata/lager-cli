"""
    lager.testrun.commands

    Commands for flashing an image to a DUT and collecting results
"""
import math
import time
import click
from ..context import get_default_gateway
from ..reset.commands import do_reset
from ..uart.commands import do_uart
from ..flash.commands import do_flash
from ..reset.commands import do_reset
from ..paramtypes import BinfileType
from ..util import stream_output
from ..status import run_job_output

@click.command()
@click.pass_context
@click.option('--gateway', required=False, help='ID of gateway to which DUT is connected')
@click.option('--serial-device', help='Gateway serial port device path', metavar='path')
@click.option('--baudrate', help='Serial baud rate', type=int, default=None)
@click.option('--bytesize', help='Number of data bits', type=click.Choice(['5', '6', '7', '8']), default=None)
@click.option('--parity', help='Parity check', type=click.Choice(['none', 'even', 'odd', 'mark', 'space']), default=None)
@click.option('--stopbits', help='Number of stop bits', type=click.Choice(['1', '1.5', '2']), default=None)
@click.option('--xonxoff/--no-xonxoff', default=None, help='Enable/disable software XON/XOFF flow control')
@click.option('--rtscts/--no-rtscts', default=None, help='Enable/disable hardware RTS/CTS flow control')
@click.option('--dsrdtr/--no-dsrdtr', default=None, help='Enable/disable hardware DSR/DTR flow control')
@click.option('--test-runner', help='End the UART session when end-of-test is detected', type=click.Choice(['unity']), default=None)
@click.option('--message-timeout', help='Message timeout', type=click.INT, default=None)
@click.option('--overall-timeout', help='Overall timeout', type=click.INT, default=None)
@click.option(
    '--hexfile',
    multiple=True, type=click.Path(exists=True),
    help='Hexfile(s) to flash. May be passed multiple times; files will be flashed in order.')
@click.option(
    '--binfile',
    multiple=True, type=BinfileType(exists=True),
    help='Binfile(s) to flash. Syntax: --binfile `<filename>,<address>` '
         'May be passed multiple times; files will be flashed in order.')
@click.option(
    '--preverify/--no-preverify',
    help='If true, only flash target if image differs from current flash contents',
    default=True)
@click.option('--verify/--no-verify', help='Verify image successfully flashed', default=True)
def testrun(ctx, gateway, serial_device, baudrate, bytesize, parity, stopbits, xonxoff, rtscts,
            dsrdtr, test_runner, message_timeout, overall_timeout, hexfile, binfile, preverify, verify):
    """
        Flash and run test on a DUT connected to a gateway
    """
    if message_timeout is None:
        message_timeout = math.inf
    if overall_timeout is None:
        overall_timeout = math.inf

    if gateway is None:
        gateway = get_default_gateway(ctx)
    session = ctx.obj.session
    resp = do_reset(session, gateway, halt=True)
    stream_output(resp)

    resp = do_uart(ctx, gateway, serial_device, baudrate, bytesize, parity, stopbits, xonxoff, rtscts, dsrdtr, test_runner)
    test_run = resp.json()

    resp = do_flash(session, gateway, hexfile, binfile, preverify, verify)
    stream_output(resp)

    resp = do_reset(ctx.obj.session, gateway, halt=False)
    stream_output(resp)


    job_id = test_run['test_run']['id']
    click.echo('Job id: {}'.format(job_id))
    connection_params = ctx.obj.websocket_connection_params(socktype='job', job_id=job_id)
    run_job_output(connection_params, message_timeout, overall_timeout, ctx.obj.debug)




# def do_flash(session, gateway, hexfile, binfile, preverify, verify, force=False):
#     """
#         Perform the actual flash operation
#     """
#     url = 'gateway/{}/flash-duck'.format(gateway)
#     files = list(zip(itertools.repeat('hexfile'), [open(path, 'rb') for path in hexfile]))
#     files.extend(
#         zip(itertools.repeat('binfile'), [open(binf.path, 'rb') for binf in binfile])
#     )
#     files.extend(
#         zip(itertools.repeat('binfile_address'), [binf.address for binf in binfile])
#     )
#     files.append(('preverify', preverify))
#     files.append(('verify', verify))
#     files.append(('force', force))

#     return session.post(url, files=files, stream=True)
