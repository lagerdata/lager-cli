"""
    lager.config

    Config file management routines
"""
import os
import configparser
import click

DEFAULT_CONFIG_FILE_NAME = '.lager'
_LAGER_CONFIG_FILE_NAME = os.getenv('LAGER_CONFIG_FILE_NAME', DEFAULT_CONFIG_FILE_NAME)

def _get_config_file_path():
    return os.path.join(os.path.expanduser('~'), _LAGER_CONFIG_FILE_NAME)

def read_config_file():
    """
        Read our config file into `config` object
    """
    config = configparser.SafeConfigParser()
    try:
        with open(_get_config_file_path()) as f:
            config.read_file(f)
    except FileNotFoundError:
        pass

    if 'LAGER' not in config:
        config.add_section('LAGER')
    return config

def write_config_file(config):
    """
        Write out `config` into our config file
    """
    with open(_get_config_file_path(), 'w') as f:
        config.write(f)


def devenv_section(name):
    return f'DEVENV.{name}'

def find_scoped_devenv(config, scope):
    scoped_names = get_devenv_names(config, target_source_dir=scope)
    if not scoped_names:
        raise click.UsageError(
            f'No development environments defined for {scope}',
        )
    if len(scoped_names) > 1:
        raise click.UsageError(
            f'Multiple development environments defined. Please specify one of: {", ".join(scoped_names)} ; using --name.',
        )
    return scoped_names[0]

def figure_out_devenv(name):
    config = read_config_file()
    if name is None:
        all_devenvs = get_devenv_names(config)
        if len(all_devenvs) == 1:
            name = all_devenvs[0]
        else:
            name = find_scoped_devenv(config, os.getcwd())

    section = devenv_section(name)
    if not config.has_section(section):
        raise click.UsageError(
            f'Development environment {name} not defined',
        )
    return config, config[section]

def get_devenv_names(config, target_source_dir=None):
    all_sections = [s for s in config.sections() if s.startswith('DEVENV.')]
    if target_source_dir and len(all_sections) > 1:
        all_sections = [
            s for s in all_sections if target_source_dir.startswith(config.get(s, 'source_dir'))
        ]
    return [s.split('.', 1)[1] for s in all_sections]

def add_devenv_command(section, command_name, command, warn):
    key = f'cmd.{command_name}'
    if key in section and warn:
        click.echo(f'Command `{command_name}` already exists, overwriting. ', nl=False, err=True)
        click.echo(f'Previous value: {section[key]}', err=True)
    section[key] = command

def remove_devenv_command(section, command_name):
    """
        Delete a named command
    """
    key = f'cmd.{command_name}'
    if key not in section:
        click.secho(f'Command `{command_name}` does not exist.', fg='red', err=True)
        click.get_current_context().exit(1)
    del section[key]


def all_commands(section):
    return {
        k.split('.', 1)[1]: section[k] for k in section.keys() if k.startswith('cmd.')
    }
