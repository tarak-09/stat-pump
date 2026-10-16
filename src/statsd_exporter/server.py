import asyncio
import logging
from aiohttp import web
from typing import Tuple
from .aggregator import Aggregator
from .parser import parse_statsd_message

logger = logging.getLogger(__name__)

class StatsdUDPProtocol(asyncio.DatagramProtocol):
    def __init__(self, aggregator: Aggregator):
        self.aggregator = aggregator

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        try:
            message = data.decode('utf-8')
            metrics = parse_statsd_message(message)
            for metric in metrics:
                self.aggregator.process_metric(metric)
        except Exception as e:
            logger.error(f"Error processing datagram from {addr}: {e}")

AGGREGATOR_KEY = web.AppKey("aggregator", Aggregator)

async def metrics_handler(request):
    aggregator = request.app[AGGREGATOR_KEY]
    metrics_data = aggregator.scrape()
    return web.Response(text=metrics_data, content_type='text/plain')

async def health_handler(request):
    return web.Response(text="OK")

async def start_servers(udp_host: str, udp_port: int, http_host: str, http_port: int) -> Tuple[asyncio.Transport, web.AppRunner]:
    aggregator = Aggregator()
    
    # Setup HTTP Server
    app = web.Application()
    app[AGGREGATOR_KEY] = aggregator
    app.router.add_get('/metrics', metrics_handler)
    app.router.add_get('/health', health_handler)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, http_host, http_port)
    await site.start()
    logger.info(f"Prometheus metrics available on http://{http_host}:{http_port}/metrics")
    
    # Setup UDP Server
    loop = asyncio.get_running_loop()
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: StatsdUDPProtocol(aggregator),
        local_addr=(udp_host, udp_port)
    )
    logger.info(f"Listening for StatsD UDP on {udp_host}:{udp_port}")
    
    return transport, runner

async def stop_servers(transport: asyncio.Transport, runner: web.AppRunner):
    transport.close()
    await runner.cleanup()
