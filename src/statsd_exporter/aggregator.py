import threading
import math
from typing import Dict, List, Tuple
from collections import defaultdict
from .parser import Metric

TagsTuple = Tuple[Tuple[str, str], ...]

class Aggregator:
    def __init__(self):
        self._lock = threading.Lock()
        
        # metric_name -> tags -> value
        self.counters: Dict[str, Dict[TagsTuple, float]] = defaultdict(lambda: defaultdict(float))
        self.gauges: Dict[str, Dict[TagsTuple, float]] = defaultdict(lambda: defaultdict(float))
        
        # metric_name -> tags -> list of values since last scrape
        self.timer_values: Dict[str, Dict[TagsTuple, List[float]]] = defaultdict(lambda: defaultdict(list))
        # metric_name -> tags -> cumulative sum
        self.timer_sums: Dict[str, Dict[TagsTuple, float]] = defaultdict(lambda: defaultdict(float))
        # metric_name -> tags -> cumulative count
        self.timer_counts: Dict[str, Dict[TagsTuple, int]] = defaultdict(lambda: defaultdict(int))
        
    def _dict_to_tags(self, tags: Dict[str, str]) -> TagsTuple:
        return tuple(sorted(tags.items()))

    def process_metric(self, metric: Metric):
        try:
            val_float = float(metric.value)
        except ValueError:
            return

        tags = self._dict_to_tags(metric.tags)

        with self._lock:
            if metric.type == 'c':
                # Counters are adjusted by sample rate
                adjusted_val = val_float / metric.sample_rate if metric.sample_rate > 0 else 0
                self.counters[metric.name][tags] += adjusted_val
                
            elif metric.type == 'g':
                if metric.value.startswith('+') or metric.value.startswith('-'):
                    self.gauges[metric.name][tags] += val_float
                else:
                    self.gauges[metric.name][tags] = val_float
                    
            elif metric.type == 'ms':
                self.timer_values[metric.name][tags].append(val_float)
                self.timer_sums[metric.name][tags] += val_float
                self.timer_counts[metric.name][tags] += 1

    def scrape(self) -> str:
        """Expose all metrics in Prometheus text format."""
        lines = []
        with self._lock:
            # Counters
            for name, tag_data in self.counters.items():
                lines.append(f"# TYPE {name} counter")
                for tags, val in tag_data.items():
                    tag_str = self._format_tags(tags)
                    lines.append(f"{name}{tag_str} {val}")
                    
            # Gauges
            for name, tag_data in self.gauges.items():
                lines.append(f"# TYPE {name} gauge")
                for tags, val in tag_data.items():
                    tag_str = self._format_tags(tags)
                    lines.append(f"{name}{tag_str} {val}")
                    
            # Timers
            for name, tag_data in self.timer_values.items():
                lines.append(f"# TYPE {name} summary")
                for tags, values in tag_data.items():
                    tag_str_base = self._format_tags(tags)
                    tag_str_50 = self._format_tags_with_extra(tags, {"quantile": "0.5"})
                    tag_str_90 = self._format_tags_with_extra(tags, {"quantile": "0.9"})
                    tag_str_99 = self._format_tags_with_extra(tags, {"quantile": "0.99"})
                    
                    if values:
                        sorted_vals = sorted(values)
                        p50 = self._percentile(sorted_vals, 0.5)
                        p90 = self._percentile(sorted_vals, 0.9)
                        p99 = self._percentile(sorted_vals, 0.99)
                    else:
                        p50 = p90 = p99 = float('nan')
                        
                    lines.append(f"{name}{tag_str_50} {p50}")
                    lines.append(f"{name}{tag_str_90} {p90}")
                    lines.append(f"{name}{tag_str_99} {p99}")
                    
                    # Clear values for next scrape
                    values.clear()
                    
                    # Add sum and count
                    cum_sum = self.timer_sums[name][tags]
                    cum_count = self.timer_counts[name][tags]
                    lines.append(f"{name}_sum{tag_str_base} {cum_sum}")
                    lines.append(f"{name}_count{tag_str_base} {cum_count}")

        lines.append("") # End with newline
        return "\n".join(lines)

    def _format_tags(self, tags: TagsTuple) -> str:
        if not tags:
            return ""
        tag_parts = [f'{k}="{self._escape_tag(v)}"' for k, v in tags]
        return "{" + ",".join(tag_parts) + "}"
        
    def _format_tags_with_extra(self, tags: TagsTuple, extra: Dict[str, str]) -> str:
        all_tags = dict(tags)
        all_tags.update(extra)
        tag_parts = [f'{k}="{self._escape_tag(str(v))}"' for k, v in all_tags.items()]
        return "{" + ",".join(tag_parts) + "}"

    def _escape_tag(self, val: str) -> str:
        return val.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')

    def _percentile(self, sorted_values: List[float], percentile: float) -> float:
        if not sorted_values:
            return float('nan')
        k = (len(sorted_values) - 1) * percentile
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return sorted_values[int(k)]
        d0 = sorted_values[int(f)] * (c - k)
        d1 = sorted_values[int(c)] * (k - f)
        return d0 + d1
