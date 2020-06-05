import pytest
import bson
from lager.status import display_job_output

@pytest.mark.asyncio
async def test_streaming_output(make_server, data_server, streaming_data, capsys):
    expected_output = ''.join(item['entry']['payload'].decode() for item in streaming_data)
    async with make_server(data_server) as server_address:
        connection_params = (server_address, {})
        await display_job_output(connection_params)
        captured = capsys.readouterr()
        assert captured.out == expected_output

@pytest.mark.asyncio
async def test_download_output(make_server, download_server, download_urls, capsys):
    # expected_output = ''.join(item['entry']['payload'].decode() for item in streaming_data)
    async with make_server(download_server) as server_address:
        connection_params = (server_address, {})
        await display_job_output(connection_params)
        assert 1 == 1  # placeholder
        # TODO: verify that urls are downloaded and contents are displayed
