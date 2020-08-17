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

_GPIO_CHOICES = click.IntRange(0, 3)
_LEVEL_CHOICES = click.Choice(('LOW', 'HIGH'), case_sensitive=False)

@gpio.command(name='set')
@click.option('--gateway', required=False, help='ID of gateway to which DUT is connected')
@click.argument('gpio_', metavar='GPIO', type=_GPIO_CHOICES)
@click.argument('type_', type=click.Choice(('IN', 'OUT'), case_sensitive=False))
@click.option('--pull', type=click.Choice(('UP', 'DOWN', 'OFF'), case_sensitive=False), default='OFF', show_default=True, help='Sets or clears the internal GPIO pull-up/down resistor.')
@click.pass_context
def set_(ctx, gateway, gpio_, type_, pull):
    """
        Sets pin GPIO mode (input/output)

        If type is IN, --pull controls the internal GPIO pull-up/down resistor.
        Otherwise it has no effect.

        GPIO can be 0, 1, 2, or 3
    """
    if gateway is None:
        gateway = get_default_gateway(ctx)

    if type_ == 'OUT' and pull != 'OFF':
        click.echo(f'GPIO pin {gpio_} set as output, ignoring --pull', err=True)

    ctx.obj.session.gpio_set(gateway, gpio_, type_, pull)


@gpio.command(name='input')
@click.option('--gateway', required=False, help='ID of gateway to which DUT is connected')
@click.argument('gpio_', metavar='GPIO', type=_GPIO_CHOICES)
@click.pass_context
def input_(ctx, gateway, gpio_):
    """
        Returns GPIO level (0 for low, 1 for high)

        GPIO can be 0, 1, 2, or 3
    """
    if gateway is None:
        gateway = get_default_gateway(ctx)
    result = ctx.obj.session.gpio_input(gateway, gpio_)
    click.echo(result.json()['level'])


@gpio.command()
@click.option('--gateway', required=False, help='ID of gateway to which DUT is connected')
@click.argument('gpio_', metavar='GPIO', type=_GPIO_CHOICES)
@click.argument('level', type=_LEVEL_CHOICES)
@click.pass_context
def output(ctx, gateway, gpio_, level):
    """
        Sets GPIO level.

        GPIO can be 0, 1, 2, or 3
    """
    if gateway is None:
        gateway = get_default_gateway(ctx)
    ctx.obj.session.gpio_output(gateway, gpio_, level)

@gpio.command()
@click.option('--gateway', required=False, help='ID of gateway to which DUT is connected')
@click.argument('gpio_', metavar='GPIO', type=_GPIO_CHOICES)
@click.option('--pulsewidth', type=click.IntRange(500, 2500), help='500 (most anti-clockwise) - 2500 (most clockwise).')
@click.option('--stop', is_flag=True, default=False, help='Stops servo pulses on the GPIO')
@click.pass_context
def servo(ctx, gateway, gpio_, pulsewidth, stop):
    """
        Starts (--pulsewidth 500-2500) or stops (--stop) servo pulses on the GPIO.
        The pulsewidths supported by servos varies and should probably be determined by experiment.
        A value of 1500 should always be safe and represents the mid-point of rotation.
        You can DAMAGE a servo if you command it to move beyond its limits.

        GPIO can be 0, 1, 2, or 3
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
    ctx.obj.session.gpio_servo(gateway, gpio_, pulsewidth, stop)

@gpio.command()
@click.option('--gateway', required=False, help='ID of gateway to which DUT is connected')
@click.argument('gpio_', metavar='GPIO', type=_GPIO_CHOICES)
@click.option('--pulse-length', type=click.IntRange(1, 100), help='Pulse length in microseconds (1-100)', required=True)
@click.option('--level', type=_LEVEL_CHOICES, help='Pulse level', required=True)
@click.pass_context
def trigger(ctx, gateway, gpio_, pulse_length, level):
    """
        Send a trigger pulse to GPIO.
        The GPIO is set to level for pulse-length microseconds and then reset to not level.

        GPIO can be 0, 1, 2, or 3
    """
    if gateway is None:
        gateway = get_default_gateway(ctx)
    ctx.obj.session.gpio_trigger(gateway, gpio_, pulse_length, level)

@gpio.command()
@click.option('--gateway', required=False, help='ID of gateway to which DUT is connected')
@click.option('--frequency', type=click.IntRange(0, 187_500_000), help='Frequency in Hz (1-187.5M or 0 for off)', required=True)
@click.option('--dutycycle', type=click.IntRange(0, 1_000_000), help='Duty cycle. 0 (off) to 1,000,000 (fully on).', required=True)
@click.pass_context
def hardware_pwm(ctx, gateway, frequency, dutycycle):
    """
        Starts hardware PWM on GPIO lines 1 and 3 at the specified frequency and dutycycle.

        Frequencies above 30MHz are unlikely to work.

        The actual number of steps beween off and fully on is the integral part of 375M/frequency

        The actual frequency set is 375M/steps

        There will only be a million steps for a frequency of 375.
        Lower frequencies will have more steps and higher frequencies will have fewer steps.
        --dutycycle is automatically scaled to take this into account.
    """
    if gateway is None:
        gateway = get_default_gateway(ctx)
    ctx.obj.session.gpio_hardware_pwm(gateway, frequency, dutycycle)


@gpio.command()
@click.option('--gateway', required=False, help='ID of gateway to which DUT is connected')
@click.argument('frequency', type=click.INT, required=True)
@click.pass_context
def hardware_clock(ctx, gateway, frequency):
    """
        Starts hardware clock on GPIO line 0 (PWM with 50% duty cycle)

        FREQUENCY can be 0 for off, or an integer between 13,184 and 375,000,000

        Frequencies above 30MHz are unlikely to work.
    """
    if frequency != 0 and (frequency < 13184 or frequency > 375_000_000):
        click.echo('Frequency must be 0 (off) or between 13,184 - 375,000,000')
        ctx.exit(1)
    if gateway is None:
        gateway = get_default_gateway(ctx)
    ctx.obj.session.gpio_hardware_clock(gateway, frequency)
