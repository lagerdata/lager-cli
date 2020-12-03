"""
    lager.adc.commands

    ADC (analog/digital converter) commands
"""

import click
from ..context import get_default_gateway
from ..paramtypes import ADCChannelType
from ..util import stream_output

@click.group(name='adc')
def adc():
    """
        Lager adc commands
    """
    pass

_RESULT_COUNT = click.Choice(('1', '4', '8', '12', '16'))
_AVERAGE_COUNT = click.Choice(('none', '1', '4', '8', '16', '32'))
_OUTPUT_TYPE = click.Choice(('raw', 'mV'), case_sensitive=False)

def _get_default_average_count():
    # TODO: implement
    return 1

def _get_default_result_count():
    # TODO: implement
    return 1

def _get_default_output():
    # TODO: implement
    return 'raw'

@adc.command()
@click.pass_context
@click.option('--gateway', required=False, help='ID of gateway to which DUT is connected')
@click.option('--average-count', required=False, type=_AVERAGE_COUNT, help='Averaging count')
@click.option('--result-count', type=_RESULT_COUNT, required=False, help='Number of results to return in single-channel mode')
@click.option('--output', type=_OUTPUT_TYPE, required=False, help='Output mode')
@click.option('-f', '--follow', required=False, default=False, is_flag=True, help='Stream output')
@click.argument('CHANNEL', type=ADCChannelType(), required=True)
def read(ctx, gateway, average_count, result_count, output, follow, channel):
    """
        Say hello to gateway
    """
    if gateway is None:
        gateway = get_default_gateway(ctx)

    if average_count is None:
        average_count = _get_default_average_count()
    else:
        if average_count.lower() == 'none':
            average_count = None
        else:
            average_count = int(average_count, 10)

    if result_count is None:
        result_count = _get_default_result_count()
    else:
        result_count = int(result_count, 10)

    if output is None:
        output = _get_default_output()
    else:
        output = output.lower()

    session = ctx.obj.session
    resp = session.read_adc(gateway, channel, average_count, result_count, output, follow)
    if follow:
        stream_output(resp)
    else:
        print(resp.json())


@adc.command()
@click.pass_context
@click.option('--gateway', required=False, help='ID of gateway to which DUT is connected')
def settings(ctx, gateway):
    pass
