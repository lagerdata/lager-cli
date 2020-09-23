.. _connecting:
.. highlight:: console

Connect to your Device Under Test
=================================

If any step below results in an error, please contact us at `support@lagerdata.com <mailto:support@lagerdata.com>`_


Once you've :ref:`logged in<quickstart>` and confirmed that your gateway is receiving commands, you'll need to connect to your DUT. We'll do this using the ``lager connect`` command. This command lets the Lager Gateway know what kind of device it is connected to, and how it is connected. For brevity we'll omit the ``--gateway <name>`` flag, but you'll need to include it if you have more than one gateway.

Connect flags
-------------

``--device``
~~~~~~~~~~~~

Identifies the Device Under Test which is connected to your gateway. See below for a list of supported devices. Example usage: ``lager connect --device nrf52``.

.. autodata:: lager_cli.SUPPORTED_DEVICES

``--transport``
~~~~~~~~~~~~~~~

TODO

``--interface``
~~~~~~~~~~~~~~~

TODO

``--speed``
~~~~~~~~~~~~

Adapter speed in kHz. This may be omitted, in which case the Lager Gateway will attempt to determine the speed automatically.



Putting it all together
~~~~~~~~~~~~~~~~~~~~~~~

``lager connect --device nrf52 --transport swd --interface ftdi --speed 4000``

::

    ➜  ~ lager connect --device nrf52 --transport swd --interface ftdi --speed 4000
    Connected!

Verify connection
~~~~~~~~~~~~~~~~~

Finally, we'll want to verify that our debugger is up and running. For that we'll use ``lager gateway status``.

::

    ➜  ~ lager gateway status
    Debugger running: True
    ---- Debugger config ----
    set ENABLE_ACQUIRE 0
    interface: ftdi_2232
    transport select swd
    target: nrf52
    ---- Logs ----
    0
    Info : FTDI SWD mode enabled
    swd
    Info : Listening on port 6666 for tcl connections
    Info : Listening on port 4444 for telnet connections
    Info : clock speed 1000 kHz
    Info : SWD DPIDR 0x2ba01477
    Info : nrf52.cpu: hardware has 6 breakpoints, 4 watchpoints
    Info : starting gdb server for nrf52.cpu on 3333
    Info : Listening on port 3333 for gdb connections
