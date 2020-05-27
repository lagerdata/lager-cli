"""
    lager.status.commands

    Status commands
"""
import click
from lager.status import run_job_output

@click.group(name='job')
def job():
    """
        Lager job commands
    """
    pass

@job.command()
@click.pass_context
@click.argument('job_id')
def status(ctx, job_id):
    """
        Get job status
    """
    connection_params = ctx.obj.websocket_connection_params(socktype='job', job_id=job_id)
    run_job_output(connection_params)
