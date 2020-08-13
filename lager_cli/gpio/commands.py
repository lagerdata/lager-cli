"""
    lager.gpio.commands

    Commands for manipulating gateway GPIO lines
"""
import click
from ..context import get_default_gateway

@click.group()
def gpio():
    """
        Lager gpio commands
    """
    pass

_GPIO_CHOICES = click.Choice(('0', '1', '2', '3'))

@gpio.command(name='set')
@click.option('--gateway', required=False, help='ID of gateway to which DUT is connected')
@click.argument('num', type=_GPIO_CHOICES)
@click.argument('type_', type=click.Choice(['IN', 'OUT'], case_sensitive=False))
@click.pass_context
def set_(ctx, gateway, num, type_):
    """
        Set GPIO type (input / output)
    """
    if gateway is None:
        gateway = get_default_gateway(ctx)

    return ctx.obj.session.gpio_set(gateway, num, type_)


@gpio.command(name='input')
@click.option('--gateway', required=False, help='ID of gateway to which DUT is connected')
@click.argument('num', type=_GPIO_CHOICES)
@click.pass_context
def input_(ctx, gateway, num):
    """
        Read from specified GPIO line
    """
    if gateway is None:
        gateway = get_default_gateway(ctx)
    return ctx.obj.session.gpio_input(gateway, num)

@gpio.command()
@click.option('--gateway', required=False, help='ID of gateway to which DUT is connected')
@click.argument('num', type=_GPIO_CHOICES)
@click.argument('value', type=click.Choice(('LOW', 'HIGH')))
@click.pass_context
def output(ctx, gateway, num, value):
    """
        Output the specified value to the specified GPIO line
    """
    if gateway is None:
        gateway = get_default_gateway(ctx)
    return ctx.obj.session.gpio_output(gateway, num, value)
