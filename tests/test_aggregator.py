import pytest
from statsd_exporter.aggregator import Aggregator
from statsd_exporter.parser import Metric

def test_aggregator_counters():
    agg = Aggregator()
    agg.process_metric(Metric(name="login", value="1", type="c"))
    agg.process_metric(Metric(name="login", value="2", type="c"))
    
    # Check simple increment
    metrics = agg.scrape()
    assert "login 3.0" in metrics
    
    # Counter with sample rate
    agg.process_metric(Metric(name="requests", value="1", type="c", sample_rate=0.1))
    metrics = agg.scrape()
    assert "requests 10.0" in metrics

def test_aggregator_gauges():
    agg = Aggregator()
    agg.process_metric(Metric(name="cpu", value="50.5", type="g"))
    assert "cpu 50.5" in agg.scrape()
    
    # Overwrite gauge
    agg.process_metric(Metric(name="cpu", value="60", type="g"))
    assert "cpu 60.0" in agg.scrape()
    
    # Relative increments
    agg.process_metric(Metric(name="cpu", value="+5", type="g"))
    assert "cpu 65.0" in agg.scrape()
    
    agg.process_metric(Metric(name="cpu", value="-10", type="g"))
    assert "cpu 55.0" in agg.scrape()

def test_aggregator_timers():
    agg = Aggregator()
    agg.process_metric(Metric(name="latency", value="100", type="ms"))
    agg.process_metric(Metric(name="latency", value="200", type="ms"))
    
    metrics = agg.scrape()
    assert 'latency{quantile="0.5"} 150.0' in metrics
    assert 'latency{quantile="0.9"} 190.0' in metrics
    assert 'latency_sum 300.0' in metrics
    assert 'latency_count 2' in metrics
    
    # Check that percentiles are cleared after scrape
    metrics2 = agg.scrape()
    assert 'latency{quantile="0.5"} nan' in metrics2
    assert 'latency_sum 300.0' in metrics2
    assert 'latency_count 2' in metrics2

def test_aggregator_tags():
    agg = Aggregator()
    agg.process_metric(Metric(name="login", value="1", type="c", tags={"env": "prod", "region": "us"}))
    metrics = agg.scrape()
    assert 'login{env="prod",region="us"} 1.0' in metrics
