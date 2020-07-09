import click

def stream_output(response):
    """
        Stream an http response to stdout
    """
    for chunk in response.iter_content(chunk_size=8):
        click.echo(chunk, nl=False)
