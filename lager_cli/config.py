"""
    lager.config

    Config file management routines
"""
import os
import configparser
import click

DEFAULT_CONFIG_FILE_NAME = '.lager'
_LAGER_CONFIG_FILE_NAME = os.getenv('LAGER_CONFIG_FILE_NAME', DEFAULT_CONFIG_FILE_NAME)

DEVENV_SECTION_NAME = 'DEVENV'


def _get_global_config_file_path():
    return make_config_path(os.path.expanduser('~'))

def make_config_path(directory, config_file_name=None):
    if config_file_name is None:
        config_file_name = _LAGER_CONFIG_FILE_NAME

    return os.path.join(directory, config_file_name)

def find_devenv_config_path():
    configs = _find_config_files()
    if not configs:
        return None
    return configs[0]

def _find_config_files():
    cwd = os.getcwd()
    cfgs = []
    global_config_file_path = _get_global_config_file_path()
    while True:
        config_path = make_config_path(cwd)
        if os.path.exists(config_path) and config_path != global_config_file_path:
            cfgs.append(config_path)
        parent = os.path.dirname(cwd)
        if parent == cwd:
            break
        cwd = parent

    return cfgs


def read_config_file(path=None):
    """
        Read our config file into `config` object
    """
    if path is None:
        path = _get_global_config_file_path()
    config = configparser.SafeConfigParser()
    try:
        with open(path) as f:
            config.read_file(f)
    except FileNotFoundError:
        pass

    if 'LAGER' not in config:
        config.add_section('LAGER')
    return config

def write_config_file(config, path=None):
    """
        Write out `config` into our config file
    """
    if path is None:
        path = _get_global_config_file_path()
    with open(path, 'w') as f:
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

def get_devenv_config():
    config_path = find_devenv_config_path()
    if config_path is None:
        click.get_current_context().exit(1)
    config = read_config_file(config_path)
    return config_path, config

