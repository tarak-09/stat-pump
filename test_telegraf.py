from statsd_exporter.parser import parse_single_metric
metric = parse_single_metric("cpu.usage,host=server1,region=us-east:85|g")
print(metric)
