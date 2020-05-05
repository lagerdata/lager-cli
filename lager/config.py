"""
    lager.config

    Config file management routines
"""
import os
import configparser

_LAGER_CONFIG_FILE_NAME = '.lager'

def _get_config_file_path():
    return os.path.join(os.path.expanduser('~'), _LAGER_CONFIG_FILE_NAME)

def read_config_file():
    """
        Read our config file into `config` object
    """
    config = configparser.ConfigParser()
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


