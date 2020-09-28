.. _recipes:
.. highlight:: console

Recipes
=======

Note: If you have multiple gateways, all commands can also take a ``--gateway`` option to specify which one. For brevity, that option is omitted from the below examples.

Stream serial output from a DUT
-------------------------------

1. List your serial ports: ``lager gateway serial-ports``.
::

    ➜  ~ lager gateway serial-ports
    /dev/ttyS0 - Lager Gateway serial port
    /dev/ttyACM0 - SEGGER VL805 USB 3.0 Host Controller; serial number 123456789
    /dev/ttyUSB1 - Future Technology Devices International, Ltd FT2232C/D/H Dual UART/FIFO IC; serial number FT1ABCDE

2. Use the serial port device name with ``lager uart`` to stream output from that serial port and save it to a file: ``lager uart --serial-device /dev/ttyACM0 --test-runner none | tee serial.log``. This will stream the output to your console and save it to a file called ``serial.log``. See the :ref:`UART command reference<uart>` for the full set of options available to ``lager uart``.
::

    ➜  ~ lager uart --serial-device /dev/ttyACM0 --test-runner none | tee serial.log
    test_mpu9250_drv.c:44:test_who_am_i_read:FAIL: Expected 113 Was 0
    test_mpu9250_drv.c:62:test_sample_rate_divider:FAIL: Expected 1 Was 0
    test_mpu9250_drv.c:79:test_enabling_disabling_fifo_modes:FAIL: Expected 1 Was 0
    test_mpu9250_drv.c:98:test_gyro_fs_select:FAIL: Expected 1 Was 0
    test_mpu9250_drv.c:36:test_42:PASS
    test_mpu9250_drv.c:37:test_blinky:PASS

    -----------------------
    6 Tests 4 Failures 0 Ignored
