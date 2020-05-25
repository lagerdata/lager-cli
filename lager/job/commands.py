"""
    lager.status.commands

    Status commands
"""
import asyncio
import click

@click.group(name='job')
def job():
    """
        Lager job commands
    """
    pass

async def read_websocket_job_data(websocket_connection):
    """
        Read
    """
    async with websocket_connection as websocket:
        data = await websocket.recv()
        print(data)

def display_job_output(websocket, loop=None):
    """
        Display job output from websocket
    """
    if loop is None:
        loop = asyncio.get_event_loop()

    loop.run_until_complete(read_websocket_job_data(websocket))

@job.command()
@click.pass_context
@click.argument('job_id')
def status(ctx, job_id):
    """
        Get job status
    """
    display_job_output(ctx.obj.websocket_connection(socktype='job', job_id=job_id))
