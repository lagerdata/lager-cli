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

@devenv.command()
@click.option('--name', prompt='Development environment name')
@click.option('--image', prompt='Docker image', default='lager/megaimage')
@click.option('--source-dir', prompt='Source code directory on host',
              default=os.getcwd, type=existing_dir_type)
@click.option('--mount-dir', prompt='Source code mount directory in docker container',
              default='/app')
def create(name, image, source_dir, mount_dir):
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

    image = config.get(section, 'image')
    source_dir = config.get(section, 'source_dir')
    mount_dir = config.get(section, 'mount_dir')
    subprocess.run([
        'docker',
        'run',
        '-it',
        '--rm',
        '-v',
        f'{source_dir}:{mount_dir}',
        image,
    ], check=True)
