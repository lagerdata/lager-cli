"""
Lager CLI
----
A Command Line Interface for Lager Data
"""

from dotenv import load_dotenv
load_dotenv()

__version__ = '0.1.1'

SUPPORTED_DEVICES = (
    'nrf52',
    'cc3220sf',
    'cc3235sf',
)
