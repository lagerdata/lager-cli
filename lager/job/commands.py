"""
    lager.status.commands

    Status commands
"""
import asyncio
import bson
import websockets
import click

@click.group(name='job')
def job():
    """
        Lager job commands
    """
    pass

async def display_job_output(connection_params):
    """
        Display job output from websocket
    """
    (uri, kwargs) = connection_params
    async with websockets.connect(uri, **kwargs) as websocket:
        async for message in websocket:
            parsed_message = bson.loads(message)['data']
            for item in parsed_message:
                entry = item['entry']
                if 'payload' in entry:
                    click.echo(entry['payload'].decode(), nl=False)

@job.command()
@click.pass_context
@click.argument('job_id')
def status(ctx, job_id):
    """
        Get job status
    """
    connection_params = ctx.obj.websocket_connection_params(socktype='job', job_id=job_id)
    asyncio.run(display_job_output(connection_params), debug=True)
