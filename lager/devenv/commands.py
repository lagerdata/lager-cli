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

def _devenv_section(name):
    return f'DEVENV.{name}'

def figure_out_devenv(name):
    config = read_config_file()
    if name is None:
        names = _get_devenv_names(config, target_source_dir=os.getcwd())
        if not names:
            raise click.UsageError(
                'No development environments defined',
            )
        if len(names) > 1:
            raise click.UsageError(
                f'Multiple development environments defined. Please specify one of: {", ".join(names)} ; using --name.',
            )
        name = names[0]

    section = _devenv_section(name)
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
    section = _devenv_section(name)
    if not config.has_section(section):
        config.add_section(section)
    config.set(section, 'image', image)
    config.set(section, 'source_dir', source_dir)
    config.set(section, 'mount_dir', mount_dir)
    config.set(section, 'shell', shell)
    write_config_file(config)

def _get_devenv_names(config, target_source_dir=None):
    all_sections = [s for s in config.sections() if s.startswith('DEVENV.')]
    if target_source_dir:
        all_sections = [
            s for s in all_sections if config.get(s, 'source_dir') == target_source_dir
        ]
    return [s.split('.', 1)[1] for s in all_sections]


@devenv.command(name='list')
def list_():
    """
        Show development environment names
    """
    config = read_config_file()
    names = _get_devenv_names(config)
    if not names:
        click.echo('No development environments defined!')
    for name in names:
        section = _devenv_section(name)
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
@click.pass_context
@click.argument('cmd_name', required=False)
@click.option('--name', required=False, help='Devenv name in which to run the command', metavar='<devenv>')
@click.option('--command', help='Raw commandline to run in docker container', metavar='<cmdline>')
@click.option('--save-as', default=None, help='Alias under which to save command specified with --command', metavar='<alias>')
def run(ctx, cmd_name, name, command, save_as):
    """
        Run CMD_NAME in a docker container. CMD_NAME is a named command which was previously saved using `--save-as`.
        If CMD_NAME is not provided, run the command specified by --command. If --save-as is also provided,
        save the command under that name for later use with CMD_NAME
    """
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


@devenv.command()
@click.argument('name', required=True, )
def delete(name):
    """
        Delete NAME

        NAME is the name of the devenv to delete. This will simply remove the named devenv from your
        Lager config and will not touch any other files on your filesystem. If the name section does
        exist it is ignored.
    """
    config = read_config_file()
    config.remove_section(_devenv_section(name))
    write_config_file(config)
