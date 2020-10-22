"""
    lager.exec.commands

    Run commands in a docker container
"""
import subprocess
import platform
import os
import click
from ..config import (
    write_config_file,
    get_global_config_file_path,
    add_devenv_command,
    get_devenv_config,
    DEVENV_SECTION_NAME,
    LAGER_CONFIG_FILE_NAME,
)
from ..context import get_ci_environment, CIEnvironment, is_container_ci

def _run_command_host(section, path, cmd_to_run, extra_args, debug):
    """
        Run a command from the host (which means, run it in a docker container)
    """
    full_command = ' '.join((cmd_to_run, *extra_args)).strip()

    image = section.get('image')
    source_dir = os.path.dirname(path)
    mount_dir = section.get('mount_dir')
    shell = section.get('shell')
    if debug:
        click.echo(full_command, err=True)
    env_vars = [var for var in os.environ if var.startswith('LAGER')]
    env_strings = [f'--env={var}={os.environ[var]}' for var in env_vars]
    base_command = ['docker', 'run', '-it', '--rm']
    base_command.extend(env_strings)

    global_config_path = get_global_config_file_path()
    if os.path.exists(global_config_path):
        base_command.extend([
            '--env=LAGER_CONFIG_FILE_DIR=/lager',
            '-v',
            f'{global_config_path}:/lager/{LAGER_CONFIG_FILE_NAME}'
        ])

    base_command.extend([
        '-v',
        f'{source_dir}:{mount_dir}',
        '-w',
        mount_dir,
        image,
        shell,
        '-c',
        full_command
    ])
    proc = subprocess.run(base_command, check=False)
    return proc.returncode

def _run_command_container(section, cmd_to_run, extra_args, debug):
    """
        Run a command directly - assume we are in a container with all necessary software
        installed already.
    """
    shell = section.get('shell')
    full_command = ' '.join((cmd_to_run, *extra_args))
    if debug:
        click.echo(full_command, err=True)
    proc = subprocess.run([shell, '-c', full_command], check=False)
    return proc.returncode

def _run_command(section, path, cmd_to_run, extra_args, debug):
    ci_env = get_ci_environment()
    if is_container_ci(ci_env):
        return _run_command_container(section, cmd_to_run, extra_args, debug)
    if ci_env == CIEnvironment.HOST:
        return _run_command_host(section, path, cmd_to_run, extra_args, debug)
    raise ValueError(f'Unknown CI environment {ci_env}')


@click.command(name='exec', context_settings={"ignore_unknown_options": True})
@click.pass_context
@click.argument('cmd_name', required=False, metavar='COMMAND')
@click.argument('extra_args', required=False, nargs=-1, metavar='EXTRA_ARGS')
@click.option('--command', help='Raw commandline to execute in docker container', metavar='\'<cmdline>\'')
@click.option('--save-as', default=None, help='Alias under which to save command specified with --command', metavar='<alias>', show_default=True)
@click.option('--warn/--no-warn', default=True, help='Whether to print a warning if overwriting an existing command.', show_default=True)
def exec_(ctx, cmd_name, extra_args, command, save_as, warn):
    """
        Execute COMMAND in a docker container. COMMAND is a named command which was previously saved using `--save-as`.
        If COMMAND is not provided, execute the command specified by --command. If --save-as is also provided,
        save the command under that name for later use with COMMAND. If EXTRA_ARGS are provided they will be appended
        to the command at runtime
    """
    if not cmd_name and not command:
        click.echo(exec_.get_help(ctx))
        ctx.exit(0)

    path, config = get_devenv_config()
    section = config[DEVENV_SECTION_NAME]

    if cmd_name and command:
        osname = platform.system()
        if osname == 'Windows':
            msg = 'If the command contains spaces, please wrap it in double quotes e.g. lager exec --command "ls -la"'
        else:
            msg = 'If the command contains spaces, please wrap it in single quotes e.g. lager exec --command \'ls -la\''
        raise click.UsageError(
            f'Cannot specify a command name and a command\n{msg}'
        )

    if cmd_name:
        key = f'cmd.{cmd_name}'
        if key not in section:
            raise click.UsageError(
                f'Command `{cmd_name}` not found',
            )
        cmd_to_run = section.get(key)
    else:
        cmd_to_run = command
        if save_as:
            add_devenv_command(section, save_as, cmd_to_run, warn)
            write_config_file(config, path)

    returncode = _run_command(section, path, cmd_to_run, extra_args, ctx.obj.debug)
    ctx.exit(returncode)
