#!/usr/bin/env python3
"""
plot_bench_interactive.py – Compare cubvec-bench vs pgvector-bench with interactive Plotly charts.

For the metric you pass on the command line (e.g. "SELECT TIME"), this script
looks inside ./cubvec-bench and ./pgvector-bench, reads every *.jsonl file, and
creates **interactive** HTML figures (one per vector dimension):

    plots/plot_dim_256_<metric>.html
    plots/plot_dim_768_<metric>.html
    plots/plot_dim_1536_<metric>.html

Hover to see exact values, drag‑select to zoom, and use the toolbar to export
PNGs if needed.

Author: 2025-06-23
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
import matplotlib.pyplot as plt

import plotly.graph_objs as go
import plotly.io as pio

# ---------------------------------------------------------------------------

CUBVEC_DIR = Path("cubvec-bench")
PGVEC_DIR = Path("pgvector-bench")
STAT_TO_USE = "avg"  # set to "min", "max" or "median" if needed

DIMENSIONS = [256, 768, 1536]  # the three plots we want
OUTPUT_TEMPLATE = "plots/plot_dim_{dim}_{metric}.html"

# Regex to capture parts of the filename
# Example: cubvec_10_250000_tbl_256_300000.jsonl
FNAME_RE = re.compile(r"^(cubvec|pgvector)_\d+_(\d+)_tbl_(\d+)_(\d+)\.jsonl$")
# groups                1 engine   2 limit   3 dim    4 rows_total


def load_folder(folder: Path, engine_tag: str, metric: str):
    """
    Scan every *.jsonl file in *folder* and collect:
        key = (dimension, sql_limit)
        val = metric_value (for STAT_TO_USE)
    Returns a dict mapping key→value.
    """
    results: dict[tuple[int, int], float] = {}
    for fp in folder.glob("*.jsonl"):
        match = FNAME_RE.match(fp.name)
        if not match:
            continue
        eng, limit, dim, _ = match.groups()
        if eng != engine_tag:
            continue

        limit = int(limit)
        dim = int(dim)

        # Read the .jsonl until we find our metric+stat line
        with fp.open() as f:
            for line in f:
                rec = json.loads(line)
                if (
                    rec["metric"] == metric
                    and rec["stat"] == STAT_TO_USE
                    and rec["limit"] == limit
                ):
                    results[(dim, limit)] = rec["value"]
                    break  # done with this file
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Generate interactive Plotly comparison charts for cubvec vs pgvector."
    )
    parser.add_argument("metric", type=str, help='Metric name, e.g. "SELECT TIME"')
    args = parser.parse_args()
    metric = args.metric

    cubvec_data = load_folder(CUBVEC_DIR, "cubvec", metric)
    pgvec_data = load_folder(PGVEC_DIR, "pgvector", metric)

    # Ensure output directory exists
    Path("plots").mkdir(exist_ok=True)

    # Plot per dimension -----------------------------------------------------
    for dim in DIMENSIONS:
        # Collect x/y for each engine
        limits = sorted(
            {lim for (d, lim) in cubvec_data.keys() if d == dim}
            | {lim for (d, lim) in pgvec_data.keys() if d == dim}
        )

        cub_y = [cubvec_data.get((dim, lim)) for lim in limits]
        pg_y = [pgvec_data.get((dim, lim)) for lim in limits]

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=limits,
                y=cub_y,
                mode="lines+markers",
                name="cubvec-bench",
                marker_symbol="circle",
            )
        )

        fig.add_trace(
            go.Scatter(
                x=limits,
                y=pg_y,
                mode="lines+markers",
                name="pgvector-bench",
                marker_symbol="square",
            )
        )

        fig.update_layout(
            title=f"{metric} vs LIMIT (dimension {dim})",
            xaxis_title="LIMIT (# rows)",
            yaxis_title=f"{metric} – {STAT_TO_USE}",
            hovermode="x unified",
            template="plotly_white",
            legend=dict(x=0.01, y=0.99),
        )

        metric_name = "_".join(metric.split(" "))
        out_html = OUTPUT_TEMPLATE.format(dim=dim, metric=metric_name)
        fig.write_html(out_html, include_plotlyjs="cdn", full_html=True)

        thumb_png = out_html.replace(".html", ".png")
        save_mpl_thumb(limits, cub_y, pg_y, metric, dim, thumb_png)
        print("✓ Saved", out_html, "and", thumb_png)

    print("All interactive plots generated.")


def save_mpl_thumb(limits, cub_y, pg_y, metric, dim, png_file):
    """Minimal static thumbnail (no extra dependencies)."""
    plt.figure(figsize=(6.4, 4.0))  # 640 × 400
    plt.plot(limits, cub_y, "-o", label="cubvec")
    plt.plot(limits, pg_y, "-s", label="pgvector")
    plt.xlabel("LIMIT (# rows)")
    plt.ylabel(f"{metric} – {STAT_TO_USE}")
    plt.title(f"{metric} vs LIMIT  (dimension {dim})")
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig(png_file, dpi=150)
    plt.close()


if __name__ == "__main__":
    main()
