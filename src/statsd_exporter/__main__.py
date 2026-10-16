import asyncio
import logging
import argparse
import os
import signal
import sys
from .server import start_servers, stop_servers

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("statsd_exporter")

async def async_main():
    parser = argparse.ArgumentParser(description="StatsD to Prometheus exporter")
    parser.add_argument("--udp-host", default=os.getenv("STATSD_UDP_HOST", "0.0.0.0"), help="UDP host to listen on")
    parser.add_argument("--udp-port", type=int, default=int(os.getenv("STATSD_UDP_PORT", 8125)), help="UDP port to listen on")
    parser.add_argument("--http-host", default=os.getenv("STATSD_HTTP_HOST", "0.0.0.0"), help="HTTP host to serve metrics")
    parser.add_argument("--http-port", type=int, default=int(os.getenv("STATSD_HTTP_PORT", 9102)), help="HTTP port to serve metrics")
    
    args = parser.parse_args()
    
    transport, runner = await start_servers(
        udp_host=args.udp_host,
        udp_port=args.udp_port,
        http_host=args.http_host,
        http_port=args.http_port
    )
    
    stop_event = asyncio.Event()
    
    def handle_signal():
        logger.info("Received stop signal")
        stop_event.set()
        
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop = asyncio.get_running_loop()
        loop.add_signal_handler(sig, handle_signal)
        
    logger.info("Daemon is running. Press Ctrl+C to stop.")
    await stop_event.wait()
    
    logger.info("Shutting down servers...")
    await stop_servers(transport, runner)
    logger.info("Shutdown complete.")

def main():
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
