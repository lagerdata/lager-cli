import pytest
import bson
from lager.status import display_job_output, InterMessageTimeout

@pytest.mark.asyncio
async def test_streaming_output(make_server, data_server, streaming_data, capsys):
    expected_output = ''.join(item['entry']['payload'].decode() for item in streaming_data)
    async with make_server(data_server) as server_address:
        connection_params = (server_address, {})
        await display_job_output(connection_params, 5, 5)
        captured = capsys.readouterr()
        assert captured.out == expected_output

@pytest.mark.asyncio
async def test_streaming_output_inter_message_timeout(make_server, data_server):
    async with make_server(data_server) as server_address:
        connection_params = (server_address, {})
        with pytest.raises(InterMessageTimeout):
            await display_job_output(connection_params, 0, 0)

@pytest.mark.asyncio
async def test_download_output(make_server, download_server, capsys, download_urls, mock_response_content):
    async with make_server(download_server) as server_address:
        connection_params = (server_address, {})
        await display_job_output(connection_params, 5, 5)
        captured = capsys.readouterr()
        assert captured.out == len(download_urls) * mock_response_content
