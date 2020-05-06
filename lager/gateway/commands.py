"""
    lager.gateway.commands

    Gateway commands
"""
import itertools
import click

@click.group()
def gateway():
    """
        Lager gateway commands
    """
    pass

@gateway.command()
@click.pass_context
@click.argument('name', required=False)
@click.option('--hexfile', multiple=True, required=True, type=click.Path(exists=True))
def flash(ctx, name, hexfile):
    """
        Flash gateway
    """
    if name is None:
        name = ctx.obj.default_gateway

    if name is None:
        hint = 'NAME. Set a default using `lager set default gateway <id>`'
        raise click.MissingParameter(
            param=flash.params[0],
            param_hint=hint,
            ctx=ctx,
            param_type='argument',
        )

    colored = ctx.obj.colored
    session = ctx.obj.session
    url = 'gateway/{}/flash-duck'.format(name)
    files = zip(itertools.repeat('hexfile'), [open(path, 'rb') for path in hexfile])
    resp = session.post(url, files=files, stream=True)
    resp.raise_for_status()
    separator = None
    in_tests = False
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
            if line.endswith(':FAIL'):
                print(colored(line, 'red'), flush=True)
            elif line.endswith(':SUCCESS'):
                print(colored(line, 'green'), flush=True)
            else:
                print(line, flush=True)
