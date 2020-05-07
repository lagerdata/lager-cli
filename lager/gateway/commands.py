"""
    lager.gateway.commands

    Gateway commands
"""
import itertools
import click

def _get_default_gateway(ctx, func):
    name = ctx.obj.default_gateway
    if name is None:
        hint = 'NAME. Set a default using `lager set default gateway <id>`'
        raise click.MissingParameter(
            param=func.params[0],
            param_hint=hint,
            ctx=ctx,
            param_type='argument',
        )
    return name

@click.group()
def gateway():
    """
        Lager gateway commands
    """
    pass

@gateway.command()
@click.pass_context
@click.argument('name', required=False)
@click.option('--model', required=True)
def serial_numbers(ctx, name, model):
    """
        Get serial numbers of devices attached to gateway
    """
    if name is None:
        name = _get_default_gateway(ctx, serial_numbers)

    session = ctx.obj.session
    url = 'gateway/{}/serial-numbers'.format(name)
    resp = session.get(url, params={'model': model})
    resp.raise_for_status()
    for serial in resp.json()['serialnums']:
        print(serial)


@gateway.command()
@click.pass_context
@click.argument('name', required=False)
@click.option('--hexfile', multiple=True, required=True, type=click.Path(exists=True))
def flash(ctx, name, hexfile):
    """
        Flash gateway
    """
    if name is None:
        name = _get_default_gateway(ctx, flash)

    colored = ctx.obj.colored
    session = ctx.obj.session
    url = 'gateway/{}/flash-duck'.format(name)
    files = zip(itertools.repeat('hexfile'), [open(path, 'rb') for path in hexfile])
    resp = session.post(url, files=files, stream=True)
    resp.raise_for_status()
    separator = None
    in_tests = False
    has_fail = False
    in_summary = False
    summary_separator = '-----------------------'
    for line in resp.iter_lines():
        if separator is None:
            separator = line
            continue
        if line == separator:
            in_tests = True
            continue
        line = line.decode()
        if not in_tests:
            print(line, flush=True)
        else:
            if line == summary_separator:
                in_summary = True
                print(line)
                continue
            if in_summary:
                color = 'red' if has_fail else 'green'
                print(colored(line, color))
            else:
                if ':FAIL' in line:
                    has_fail = True
                    print(colored(line, 'red'), flush=True)
                elif ':PASS' in line:
                    print(colored(line, 'green'), flush=True)
                elif ':INFO' in line:
                    print(colored(line, 'yellow'), flush=True)
                else:
                    print(line, flush=True)
