import pytest
import asyncio
import socket
import aiohttp
from statsd_exporter.server import start_servers, stop_servers

@pytest.mark.asyncio
async def test_server_e2e():
    transport, runner = await start_servers("127.0.0.1", 8126, "127.0.0.1", 9103)
    
    try:
        # Give servers a moment to start
        await asyncio.sleep(0.1)
        
        # Send UDP packet
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(b"test.counter:5|c|#env:test", ("127.0.0.1", 8126))
        sock.close()
        
        # Wait for processing
        await asyncio.sleep(0.1)
        
        # Check HTTP endpoint
        async with aiohttp.ClientSession() as session:
            async with session.get("http://127.0.0.1:9103/metrics") as response:
                assert response.status == 200
                text = await response.text()
                assert 'test_counter{env="test"} 5.0' in text
                
            # Check health endpoint
            async with session.get("http://127.0.0.1:9103/health") as response:
                assert response.status == 200
                text = await response.text()
                assert text == "OK"
    finally:
        await stop_servers(transport, runner)

@pytest.mark.asyncio
async def test_server_telegraf_tags():
    transport, runner = await start_servers("127.0.0.1", 8127, "127.0.0.1", 9104)
    
    try:
        await asyncio.sleep(0.1)
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(b"test.telegraf,env=prod,region=us-east:10|c", ("127.0.0.1", 8127))
        sock.close()
        
        await asyncio.sleep(0.1)
        
        async with aiohttp.ClientSession() as session:
            async with session.get("http://127.0.0.1:9104/metrics") as response:
                assert response.status == 200
                text = await response.text()
                assert 'test_telegraf{env="prod",region="us-east"} 10.0' in text
    finally:
        await stop_servers(transport, runner)
