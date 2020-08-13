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

    ctx.obj.session.gpio_set(gateway, num, type_)


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
    ctx.obj.session.gpio_input(gateway, num)


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
    ctx.obj.session.gpio_output(gateway, num, value)

@gpio.command()
@click.option('--gateway', required=False, help='ID of gateway to which DUT is connected')
@click.argument('num', type=_GPIO_CHOICES)
@click.option('--pulsewidth', type=click.IntRange(500, 2500), help='500 (most anti-clockwise) - 2500 (most clockwise).')
@click.option('--stop', is_flag=True, default=False, help='Stops servo pulses on the GPIO')
@click.pass_context
def servo(ctx, gateway, num, pulsewidth, stop):
    """
        Starts (--pulsewidth 500-2500) or stops (--stop) servo pulses on the GPIO.
        The pulsewidths supported by servos varies and should probably be determined by experiment. A value of 1500 should always be safe and represents the mid-point of rotation.
        You can DAMAGE a servo if you command it to move beyond its limits.
    """
    if stop and pulsewidth:
        click.echo(ctx.get_help(), err=True)
        click.secho('--stop and --pulsewidth both specified; please only use one', fg='red', err=True)
        ctx.exit(1)
    if not stop and not pulsewidth:
        click.echo(ctx.get_help(), err=True)
        click.secho('Please pass one of --pulsewidth or --stop', fg='red', err=True)
        ctx.exit(1)
    if gateway is None:
        gateway = get_default_gateway(ctx)
    ctx.obj.session.gpio_servo(gateway, num, pulsewidth, stop)
