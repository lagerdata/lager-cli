.. _devenvs:
.. highlight:: console

Lager Devenvs
=============

Devenvs are lightweight wrappers around Docker designed for embedded developers. A Devenv abstracts away most of the complexity of Docker for the most common use case of day-to-day embedded development: Running a command in a container with the proper working directory, with volumes properly mounted so that the container can see your source code. Note that they are entirely optional - none of the other Lager functionality requires you to use them. Most of the functionality could in theory be replicated with a sufficiently advanced bash script, but Devenvs are significantly easier to use, and we think they're pretty neat.

Benefits of using a Lager Devenv:
---------------------------------

- Quickly run commands inside a container without platform-specific shell scripting
- Save named commands commands (e.g. ``lager exec make``, ``lager exec clean``, etc) that can be shared with anyone who has access to the repo.
- Seamlessly integrates with container-based cloud build systems - Lager Devenvs automatically detect if they are running inside a container or CI system, to avoid attempting to launch containers from within a container

How does it work?
-----------------

Lager Devenvs are defined by a ``.lager`` file that lives at the root of your repo. You don't need to manually create or edit this file; the Lager CLI tool will do it for you. Since it lives in your repo, it provides an easy way to share commands with the rest of your team, and ensure that everyone is using the same image for compilation.

Getting started
---------------

First, make sure you've installed the :ref:`Lager CLI<quickstart>`. Then, cd to the top-level directory of your project. Finally, run ``lager devenv create`` to create your ``.lager`` file. This will ask two questions: the name of the Docker image you want to use, and the directory within the container where your source code should be mounted.

::

    ➜  lager devenv create
    Docker image [lagerdata/devenv-cortexm]:
    Source code mount directory in docker container [/app]:

You can use any Docker image; the default is ``lagerdata/devenv-cortexm``, which is a container with tools suitable for compiling for an ARM Cortex M. Lager also curates a `set of Dockerfiles <https://github.com/lagerdata/devenv-dockerfiles>`_ that you can use to build your own images.

Launching a terminal
--------------------

You can launch an interactive terminal session with your container via ``lager devenv terminal``. This can be useful for exploring the filesystem or manually running commands within a container.

Running your first command
--------------------------

To run a command within a container, use ``lager exec --command '<COMMAND>'`` (without the brackets, but with the single quotes). For example:

``lager exec --command 'ls -a'``
::

    ➜  lager exec --command 'ls -a'
    .     .github      .lager          README.md  linker   third_party
    ..    .gitignore   CMakeLists.txt  app        modules
    .git  .gitmodules  LICENSE.md      cmake      test

Saving commands
---------------

You can save commands for later use with the ``--save-as`` flag. This will give the command a name that can later be passed to ``lager exec``. For example, suppose we have the following: ``lager exec --save-as build --command 'mkdir -p _build; cd _build ; cmake .. -G Ninja ;cmake --build . --target blue42_test_mpu9250_drv'``. That will run the ``--command`` argument in a container, and create an alias for it called ``build``.

Running a saved command
-----------------------

Instead of passing ``--command`` to ``lager exec``, you can pass a name that was previously defined using the ``--save-as`` flag. Using the example above - if you've saved a command with the alias ``build``, you can subsequently invoke it using ``lager exec build``.

Viewing saved commands
----------------------

You can list the available commands (for use with ``lager exec``) using ``lager devenv commands``:

::

    ➜  lager devenv commands
    cmake-test1: mkdir -p _build; cd _build ; cmake .. -G Ninja; cmake --build . --target blue42_test1
    build: mkdir -p _build; cd _build ; cmake .. -G Ninja ;cmake --build . --target blue42_test_mpu9250_drv
    cmake-clean: rm -rf _build
