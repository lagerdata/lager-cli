.. highlight:: console

Quickstart
==========

Install the lager-cli package:
------------------------------

``pip3 install -U lager-cli``

Log in to Lager:
----------------
``lager login``

The lager-cli tool will prompt you to open a browser window so that you can link lager-cli to your account.
::

    ➜  ~ lager login
    Please confirm the following code appears in your browser: ABCD-EFGH-IJKL
    Lager would like to open a browser window to confirm your login info [y/N]:

If you do not have a browser installed (for example if you are using a virtual machine or docker image) lager will prompt you to copy-paste a url:

::

    ➜  ~ lager login
    Please visit https://auth.lagerdata.com/activate?user_code=ABCD-EFGH-IJKL in your browser
    And confirm your device token: ABCD-EFGH-IJKL
    Awaiting confirmation... (Could take up to 5 seconds after clicking "Confirm" in your browser)

Say hello to your gateway:
--------------------------
``lager gateway hello``

::

    ➜  ~ lager gateway hello
    Hello, world! Your gateway is connected.

If you get the "Hello, world!" message, that means your gateway is connected and ready to receive commands! If any step results in an error, please contact us at `support@lagerdata.com <mailto:support@lagerdata.com>`_
