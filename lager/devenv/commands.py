"""
    lager.devenv.commands

    Devenv commands
"""
import os
import subprocess
import click
from ..config import read_config_file, write_config_file

@click.group()
def devenv():
    """
        Lager devenv commands
    """
    pass

existing_dir_type = click.Path(
    exists=True,
    file_okay=False,
    dir_okay=True,
    readable=True,
    resolve_path=True,
)

def figure_out_devenv(name):
    config = read_config_file()
    if name is None:
        names = _get_devenv_names()
        if not names:
            raise click.UsageError(
                'No development environments defined',
            )
        if len(names) > 1:
            raise click.UsageError(
                f'Multiple development environments defined. Please specify one of: {", ".join(names)} ; using --name.',
            )
        name = names[0]

    config = read_config_file()
    section = f'DEVENV.{name}'
    if not config.has_section(section):
        raise click.UsageError(
            f'Development environment {name} not defined',
        )

    return config, config[section]

def _get_default_name():
    return os.path.split(os.getcwd())[1]

@devenv.command()
@click.option('--name', prompt='Development environment name', default=_get_default_name)
@click.option('--image', prompt='Docker image', default='lager/megaimage')
@click.option('--source-dir', prompt='Source code directory on host',
              default=os.getcwd, type=existing_dir_type)
@click.option('--mount-dir', prompt='Source code mount directory in docker container',
              default='/app')
@click.option('--shell', prompt='Path to shell executable in docker image',
              default='/bin/bash')
def create(name, image, source_dir, mount_dir, shell):
    """
        Create a development environment
    """


    config = read_config_file()
    section = f'DEVENV.{name}'
    if not config.has_section(section):
        config.add_section(section)
    config.set(section, 'image', image)
    config.set(section, 'source_dir', source_dir)
    config.set(section, 'mount_dir', mount_dir)
    config.set(section, 'shell', shell)
    write_config_file(config)

def _get_devenv_names():
    config = read_config_file()
    return [
        section.split('.', 1)[1]
        for section in config.sections()
        if section.startswith('DEVENV.')
    ]



@devenv.command(name='list')
def list_():
    """
        Show development environment names
    """
    names = _get_devenv_names()
    if not names:
        click.echo('No development environments defined!')
    for name in names:
        click.echo(name)


@devenv.command()
@click.option('--name')
def terminal(name):
    """
        Start an interactive terminal for a docker image
    """
    _, section = figure_out_devenv(name)

    image = section.get('image')
    source_dir = section.get('source_dir')
    mount_dir = section.get('mount_dir')
    subprocess.run([
        'docker',
        'run',
        '-it',
        '--rm',
        '-v',
        f'{source_dir}:{mount_dir}',
        image,
    ], check=True)


@devenv.command()
@click.pass_context
@click.argument('cmd_name', required=False)
@click.option('--name', required=False)
@click.option('--command')
@click.option('--save-as', default=None)
def run(ctx, cmd_name, name, command, save_as):
    config, section = figure_out_devenv(name)

    if not cmd_name and not command:
        raise click.UsageError(
            'Please specify a command shortcut or a command'
        )

    if cmd_name and command:
        raise click.UsageError(
            'Cannot specify a command shortcut and a command'
        )

    if cmd_name:
        key = f'cmd.{cmd_name}'
        if key not in section:
            raise click.UsageError(
                f'Command `{cmd_name}` not found',
            )
        cmd_to_run = section.get(key)
    else:
        cmd_to_run = command
        if save_as:
            section[f'cmd.{save_as}'] = cmd_to_run
            write_config_file(config)

    image = section.get('image')
    source_dir = section.get('source_dir')
    mount_dir = section.get('mount_dir')
    shell = section.get('shell')
    proc = subprocess.run([
        'docker',
        'run',
        '-it',
        '--rm',
        '-v',
        f'{source_dir}:{mount_dir}',
        image,
        shell,
        '-c',
        cmd_to_run
    ], check=False)
    ctx.exit(proc.returncode)
