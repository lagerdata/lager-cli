"""
    lager.exec.commands

    Run commands in a docker container
"""
import subprocess
import os
import click
from ..config import (
    write_config_file,
    add_devenv_command,
    get_devenv_config,
    DEVENV_SECTION_NAME,
)
from ..context import get_ci_environment, CIEnvironment

def _run_command_host(section, path, cmd_to_run):
    image = section.get('image')
    source_dir = os.path.dirname(path)
    mount_dir = section.get('mount_dir')
    shell = section.get('shell')
    proc = subprocess.run([
        'docker',
        'run',
        '-it',
        '--rm',
        '-v',
        f'{source_dir}:{mount_dir}',
        image,
        shell,
        '-c',
        cmd_to_run
    ], check=False)
    return proc.returncode

def _run_command_drone(section, cmd_to_run):
    shell = section.get('shell')
    proc = subprocess.run([shell, '-c', cmd_to_run], check=False)
    return proc.returncode

def _run_command(section, path, cmd_to_run):
    ci_env = get_ci_environment()
    if ci_env == CIEnvironment.DRONE:
        return _run_command_drone(section, cmd_to_run)
    if ci_env == CIEnvironment.HOST:
        return _run_command_host(section, path, cmd_to_run)
    raise ValueError(f'Unknown CI environment {ci_env}')


@click.command(name='exec')
@click.pass_context
@click.argument('cmd_name', required=False, metavar='COMMAND')
@click.option('--command', help='Raw commandline to execute in docker container', metavar='\'<cmdline>\'')
@click.option('--save-as', default=None, help='Alias under which to save command specified with --command', metavar='<alias>', show_default=True)
@click.option('--warn/--no-warn', default=True, help='Whether to print a warning if overwriting an existing command. Default True', show_default=True)
def exec_(ctx, cmd_name, command, save_as, warn):
    """
        Execute COMMAND in a docker container. COMMAND is a named command which was previously saved using `--save-as`.
        If COMMAND is not provided, execute the command specified by --command. If --save-as is also provided,
        save the command under that name for later use with COMMAND
    """
    path, config = get_devenv_config()
    section = config[DEVENV_SECTION_NAME]

    if not cmd_name and not command:
        click.echo(exec_.get_help(ctx))
        ctx.exit(0)

    if cmd_name and command:
        raise click.UsageError(
            'Cannot specify a command name and a command'
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

    returncode = _run_command(section, path, cmd_to_run)
    ctx.exit(returncode)
