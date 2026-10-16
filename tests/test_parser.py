import pytest
from statsd_exporter.parser import parse_statsd_message, Metric, parse_single_metric

def test_parse_single_metric_basic():
    metric = parse_single_metric("user.logins:1|c")
    assert metric == Metric(name="user_logins", value="1", type="c")

def test_parse_single_metric_with_sample_rate():
    metric = parse_single_metric("request.count:1|c|@0.1")
    assert metric == Metric(name="request_count", value="1", type="c", sample_rate=0.1)

def test_parse_single_metric_with_tags():
    metric = parse_single_metric("cpu.usage:85|g|#host:server1,region:us-east")
    assert metric.tags == {"host": "server1", "region": "us-east"}

def test_parse_single_metric_with_sample_rate_and_tags():
    metric = parse_single_metric("request.count:1|c|@0.5|#env:prod")
    assert metric.sample_rate == 0.5
    assert metric.tags == {"env": "prod"}

def test_parse_multiple_metrics():
    msg = "metric1:1|c\nmetric2:2|g\n"
    metrics = parse_statsd_message(msg)
    assert len(metrics) == 2
    assert metrics[0].name == "metric1"
    assert metrics[1].name == "metric2"

def test_parse_invalid_metrics():
    assert parse_single_metric("invalid_metric") is None
    assert parse_single_metric("metric:abc|c") is None
    assert parse_single_metric("metric:1|invalid_type") is None
