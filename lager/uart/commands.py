"""
    lager.erase.commands

    Commands for erasing a DUT
"""
import click
from ..context import get_default_gateway
from ..status import run_job_output
from ..config import read_config_file

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
@click.option('--test-matcher', help='End the UART session when end-of-test is detected', type=click.Choice(['unity']), default=None)
@click.option('--message-timeout', help='Message timeout', type=click.INT, default=None)
@click.option('--overall-timeout', help='Overall timeout', type=click.INT, default=None)
def uart(ctx, gateway, serial_device, baudrate, bytesize, parity, stopbits, xonxoff, rtscts, dsrdtr, test_matcher, message_timeout, overall_timeout):
    """
        Connect to UART on a DUT.
    """
    if serial_device is None:
        config = read_config_file()
        if 'LAGER' in config and 'serial_device' in config['LAGER']:
            serial_device = config.get('LAGER', 'serial_device')

    if not serial_device:
        raise click.UsageError(
            'serial_device required',
            ctx=ctx,
        )

    if xonxoff and rtscts:
        raise click.UsageError(
            'Cannot use xonxoff and rtscts simultaneously',
            ctx=ctx,
        )
    if gateway is None:
        gateway = get_default_gateway(ctx)

    session = ctx.obj.session
    url = 'gateway/{}/uart-duck'.format(gateway)

    serial_options = {
        'device': serial_device,
        'baudrate': baudrate,
        'bytesize': bytesize,
        'parity': parity,
        'stopbits': stopbits,
        'xonxoff': xonxoff,
        'rtscts': rtscts,
        'dsrdtr': dsrdtr,
    }
    json_data = {
        'serial_options': serial_options,
        'test_matcher': test_matcher,
    }

    resp = session.post(url, json=json_data)
    test_run = resp.json()
    job_id = test_run['test_run']['id']
    click.echo('Job id: {}'.format(job_id))
    connection_params = ctx.obj.websocket_connection_params(socktype='job', job_id=job_id)
    run_job_output(connection_params, message_timeout, overall_timeout, ctx.obj.debug)
