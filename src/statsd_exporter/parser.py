import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

@dataclass
class Metric:
    name: str
    value: str
    type: str
    sample_rate: float = 1.0
    tags: Dict[str, str] = field(default_factory=dict)

def parse_statsd_message(message: str) -> List[Metric]:
    """Parse a StatsD message, which may contain multiple metrics separated by newlines."""
    metrics = []
    for line in message.strip().split('\n'):
        line = line.strip()
        if not line:
            continue
        
        parsed = parse_single_metric(line)
        if parsed:
            metrics.append(parsed)
            
    return metrics

def parse_single_metric(line: str) -> Optional[Metric]:
    # Format: name:value|type[|@sample_rate][|#tags]
    if ':' not in line:
        return None
        
    name_part, rest = line.split(':', 1)
    
    # name formatting for prometheus (replace . and - with _)
    name = re.sub(r'[^a-zA-Z0-9_]', '_', name_part)
    
    parts = rest.split('|')
    if len(parts) < 2:
        return None
        
    value_str = parts[0]
    try:
        float(value_str)
    except ValueError:
        return None
        
    metric_type = parts[1]
    if metric_type not in ('c', 'g', 'ms'):
        return None
        
    sample_rate = 1.0
    tags = {}
    
    for part in parts[2:]:
        if part.startswith('@'):
            try:
                sample_rate = float(part[1:])
            except ValueError:
                pass
        elif part.startswith('#'):
            tag_str = part[1:]
            for tag_pair in tag_str.split(','):
                if ':' in tag_pair:
                    k, v = tag_pair.split(':', 1)
                    tags[k] = v
                else:
                    tags[tag_pair] = "true"
                    
    return Metric(
        name=name,
        value=value_str,
        type=metric_type,
        sample_rate=sample_rate,
        tags=tags
    )
