# StatsD to Prometheus Exporter

A lightweight, asynchronous Python daemon that ingests StatsD metrics via UDP, aggregates them in memory, and exposes them in the Prometheus text format via an HTTP `/metrics` endpoint. 

## Why it exists

Many legacy or simple applications rely on StatsD's fire-and-forget UDP protocol for instrumenting metrics (counters, gauges, and timers) without blocking the main application thread. However, modern monitoring stacks rely on Prometheus, which uses a pull-based HTTP model.

This exporter bridges the gap by:
- Listening for StatsD UDP packets on a configurable port.
- Parsing standard StatsD format and DogStatsD-style tags.
- Aggregating the metrics into cumulative Counters, current Gauges, and percentile-based Summaries (for Timers).
- Exposing the aggregated state on a `/metrics` HTTP endpoint for Prometheus to scrape.

## Features

- **Counters (`c`)**: Accumulates counts and applies sampling rates.
- **Gauges (`g`)**: Stores the latest value or processes relative updates (`+5`, `-2`).
- **Timers (`ms`)**: Stores raw values between scrapes to calculate min, max, count, sum, and standard percentiles (`p50`, `p90`, `p99`). To prevent unbounded memory growth, timer percentiles are cleared after each scrape, perfectly aligning with Prometheus Summary semantics.
- **Tags**: Native support for DogStatsD style tags (e.g. `metric_name:1|c|#env:prod,version:1.2.0`) and Telegraf style tags (e.g. `metric_name,env=prod,version=1.2.0:1|c`).

## Installation

This project manages dependencies using `uv` (a fast Python package installer and resolver).

```bash
# Clone the repository
# (Assuming you already have the repository)

# Install the application and its dependencies
uv sync
```

## Usage

You can run the daemon via the installed script or as a module.

```bash
uv run statsd-exporter
```

By default, the daemon listens on:
- **StatsD UDP**: `0.0.0.0:8125`
- **Prometheus HTTP**: `0.0.0.0:9102`

You can configure these using environment variables or command-line arguments:

```bash
# Using CLI arguments
uv run statsd-exporter --udp-port 8125 --http-port 9102

# Using Environment variables
STATSD_UDP_PORT=8125 STATSD_HTTP_PORT=9102 uv run statsd-exporter
```

## Worked Example

1. Start the exporter in the background:
```bash
uv run statsd-exporter &
```

2. Send some sample StatsD metrics to it via `netcat` or Python:
```bash
echo "user.logins:1|c|#env:prod" > /dev/udp/127.0.0.1/8125
echo "user.logins:2|c|#env:prod" > /dev/udp/127.0.0.1/8125
echo "cpu.usage:45.5|g|#host:web01" > /dev/udp/127.0.0.1/8125
echo "db.latency:12|ms|#table:users" > /dev/udp/127.0.0.1/8125
echo "db.latency:24|ms|#table:users" > /dev/udp/127.0.0.1/8125
echo "db.latency:36|ms|#table:users" > /dev/udp/127.0.0.1/8125
echo "mem.usage,host=web01,region=us-east:1024|g" > /dev/udp/127.0.0.1/8125
```

3. Scrape the Prometheus `/metrics` endpoint:
```bash
curl -s http://127.0.0.1:9102/metrics
```

**Expected Output:**
```text
# TYPE user_logins counter
user_logins{env="prod"} 3.0
# TYPE cpu_usage gauge
cpu_usage{host="web01"} 45.5
# TYPE mem_usage gauge
mem_usage{host="web01",region="us-east"} 1024.0
# TYPE db_latency summary
db_latency{quantile="0.5",table="users"} 24.0
db_latency{quantile="0.9",table="users"} 33.6
db_latency{quantile="0.99",table="users"} 35.76
db_latency_sum{table="users"} 72.0
db_latency_count{table="users"} 3
```

## Running Tests

Tests are written using `pytest` and `pytest-asyncio`. 

To run the test suite:

```bash
uv run pytest
```

To run with coverage:
```bash
uv run pytest --cov=src tests/
```
