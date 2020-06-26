"""
    lager.run.commands

    Run commands in a docker container
"""
import os
import subprocess
import click
from ..config import read_config_file, write_config_file, figure_out_devenv

@click.command()
@click.pass_context
@click.argument('cmd_name', required=False, metavar='COMMAND')
@click.option('--devenv', help='devenv in which to run the command', metavar='<devenv>')
@click.option('--command', help='Raw commandline to run in docker container', metavar='\'<cmdline>\'')
@click.option('--save-as', default=None, help='Alias under which to save command specified with --command', metavar='<alias>')
def run(ctx, cmd_name, devenv, command, save_as):
    """
        Run COMMAND in a docker container. COMMAND is a named command which was previously saved using `--save-as`.
        If COMMAND is not provided, run the command specified by --command. If --save-as is also provided,
        save the command under that name for later use with COMMAND
    """
    config, section = figure_out_devenv(devenv)
    if not cmd_name and not command:
        click.echo(run.get_help(ctx))
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
            section[f'cmd.{save_as}'] = cmd_to_run
            write_config_file(config)

    image = section.get('image')
    source_dir = section.get('source_dir')
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
    ctx.exit(proc.returncode)
