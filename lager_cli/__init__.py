"""
Lager CLI
----
A Command Line Interface for Lager Data
"""

__version__ = '0.1.28'

SUPPORTED_DEVICES = (
    'nrf52',
    'cc3220sf',
    'cc3235sf',
    'cc3220s',
    'atsame70',
    'efm32',
    'stm32f0x',
    'stm32f1x',
    'stm32f2x',
    'stm32f3x',
    'stm32f4x',
    'stm32f7x',
    'stm32g0x',
    'stm32g4x',
    'stm32h7x',
    'stm32h7x_dual_bank',
    'stm32l0',
    'stm32l0_dual_bank',
    'stm32l1',
    'stm32l1x_dual_bank',
    'stm32l4x',
    'stm32mp15x',
    'stm32w108xx',
    'stm32wbx',
    'stm32wlx',
    'stm32xl',
)

SUPPORTED_INTERFACES = (
    'ftdi',
    'jlink',
    'cmsis-dap',
    'xds110',
    'stlink',
    'stlink-dap',
)
