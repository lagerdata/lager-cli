"""
    lager.auth

    Authentication helpers
"""
import os
import configparser

_LAGER_CONFIG_FILE_NAME = '.lager'

def get_config_file_path():
    """
        Return absolute path to config file
    """
    return os.path.join(os.path.expanduser('~'), _LAGER_CONFIG_FILE_NAME)


def load_auth():
    """
        Load auth token from config
    """
    config = configparser.ConfigParser()
    try:
        with open(get_config_file_path()) as f:
            config.read_file(f)
    except FileNotFoundError:
        return None

    if 'AUTH' not in config:
        return None

    return config['AUTH']
