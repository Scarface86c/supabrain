# SupaBrain Visualizations

Interactive graphs and heatmaps for memory system analysis.

## Features

### 1. Memory Growth Timeline
Stacked area chart showing memory distribution across temporal layers over time.
- **Layers:** working (red), short (teal), long (blue), archive (green)
- **Shows:** How memory accumulates and migrates between layers

### 2. Access Heatmap
Hour×day heatmap revealing memory access patterns.
- **X-axis:** Days of week (Mon-Sun)
- **Y-axis:** Hours of day (00:00-23:00)
- **Color:** Access count intensity

### 3. Top Memories Bar Chart
Horizontal bar chart of most frequently accessed memories.
- **Color coding:** By temporal layer
- **Labels:** Memory ID + summary snippet
- **Metrics:** Access count

## Usage

### CLI

```bash
# Generate all visualizations (last 30 days)
python3 memory_visualizations.py --days 30 --type all

# Just memory growth timeline
python3 memory_visualizations.py --days 14 --type growth

# Just access heatmap
python3 memory_visualizations.py --days 7 --type heatmap

# Just top memories
python3 memory_visualizations.py --type top

# Custom output directory
python3 memory_visualizations.py --output-dir /path/to/output
```

### API

```bash
# Generate all visualizations
curl "http://localhost:8080/api/v1/analytics/visualizations/generate?days=30&viz_type=all"

# Just memory growth
curl "http://localhost:8080/api/v1/analytics/visualizations/generate?days=14&viz_type=growth"

# Just heatmap
curl "http://localhost:8080/api/v1/analytics/visualizations/generate?days=7&viz_type=heatmap"

# Just top memories
curl "http://localhost:8080/api/v1/analytics/visualizations/generate?viz_type=top"
```

### Python

```python
from memory_visualizations import MemoryVisualizer

viz = MemoryVisualizer(output_dir="/tmp/graphs")

# Generate all
results = viz.generate_all_visualizations(days=30)
# Returns: {'memory_growth': '/path/to/file.png', ...}

# Individual charts
growth_path = viz.plot_memory_growth_timeline(days=30)
heatmap_path = viz.plot_access_heatmap(days=30)
top_path = viz.plot_top_memories_bar(limit=20)
```

## Requirements

- **matplotlib** (auto-installed in venv)
- PostgreSQL with SupaBrain schema

## Output

All visualizations are saved as PNG files in the configured output directory (default: `/tmp/supabrain_graphs/`).

File naming:
- `memory_growth_{days}d.png`
- `access_heatmap_{days}d.png`
- `top_memories_{limit}.png`

## Testing

```bash
# Run tests
cd /home/ubuntu/supabrain/core
source venv/bin/activate
pytest tests/test_visualizations.py -v
```

## Implementation Details

**Module:** `memory_visualizations.py`  
**Tests:** `tests/test_visualizations.py`  
**API Route:** `routes/analytics.py` → `/api/v1/analytics/visualizations/generate`  
**Dependencies:** matplotlib, psycopg2, numpy (via matplotlib)

**Database queries:**
- Memory growth: Groups `created_at` by date and `temporal_layer`
- Access heatmap: Extracts hour/day from `last_accessed` timestamp
- Top memories: Orders by `access_count DESC`

## Completed

**Date:** 2026-02-23  
**Author:** Scar (autonomous)  
**TODO:** #175  
**Duration:** 20 minutes
