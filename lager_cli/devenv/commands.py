"""
    lager.devenv.commands

    Devenv commands
"""
import os
import subprocess
import click
from ..config import (
    read_config_file,
    write_config_file,
    figure_out_devenv,
    get_devenv_names,
    devenv_section,
    add_devenv_command,
    remove_devenv_command,
    all_commands,
)

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

def _get_default_name():
    return os.path.split(os.getcwd())[1]

@devenv.command()
@click.option('--name', prompt='Development environment name', default=_get_default_name)
@click.option('--image', prompt='Docker image', default='lagerdata/cortexm-devenv')
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
    section = devenv_section(name)
    if not config.has_section(section):
        config.add_section(section)
    config.set(section, 'image', image)
    config.set(section, 'source_dir', source_dir)
    config.set(section, 'mount_dir', mount_dir)
    config.set(section, 'shell', shell)
    write_config_file(config)

@devenv.command(name='list')
def list_():
    """
        Show development environment names
    """
    config = read_config_file()
    names = get_devenv_names(config)
    if not names:
        click.echo('No development environments defined!')
    for name in names:
        section = devenv_section(name)
        click.echo(name)
        click.echo(f'\timage: {config.get(section, "image")}')
        click.echo(f'\tsource dir: {config.get(section, "source_dir")}')
        click.echo(f'\tmount dir: {config.get(section, "mount_dir")}')
        click.echo(f'\tshell: {config.get(section, "shell")}')


@devenv.command()
@click.option('--name', help='Devenv for which to launch an interactive terminal')
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
@click.argument('name', required=True)
def delete(name):
    """
        Delete NAME

        NAME is the name of the devenv to delete. This will simply remove the named devenv from your
        Lager config and will not touch any other files on your filesystem. If the name section does
        exist it is ignored.
    """
    config = read_config_file()
    config.remove_section(devenv_section(name))
    write_config_file(config)


@devenv.command()
@click.argument('command_name')
@click.argument('command', required=False)
@click.option('--devenv', '_devenv', help='Add command to devenv named `foo`', metavar='foo')
@click.option('--warn/--no-warn', default=True, help='Whether to print a warning if overwriting an existing command. Default True')
def add_command(command_name, command, _devenv, warn):
    """
        Add COMMAND to devenv with the name COMMAND_NAME
    """
    config, section = figure_out_devenv(_devenv)
    if not command:
        command = click.prompt('Please enter the command')

    add_devenv_command(section, command_name, command, warn)
    write_config_file(config)

@devenv.command()
@click.argument('command_name')
@click.option('--devenv', '_devenv', help='Delete command from devenv named `foo`', metavar='foo')
def delete_command(command_name, _devenv):
    """
        Delete COMMAND_NAME from devenv
    """
    config, section = figure_out_devenv(_devenv)

    remove_devenv_command(section, command_name)
    write_config_file(config)


@devenv.command()
@click.option('--devenv', '_devenv', help='Devenv name')
def commands(_devenv):
    """
        List the commands in a devenv
    """
    _, section = figure_out_devenv(_devenv)
    for name, command in all_commands(section).items():
        click.echo(f'{name}: {command}')
