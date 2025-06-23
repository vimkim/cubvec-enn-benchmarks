#!/usr/bin/env python3
"""
plot_bench.py  –  Compare cubvec-bench vs pgvector-bench

For the metric you pass on the command line (e.g. "SELECT TIME"),
this script looks inside ./cubvec-bench and ./pgvector-bench,
reads every *.jsonl file, and creates three figures:

    plot_dim_256.png
    plot_dim_768.png
    plot_dim_1536.png

Each figure shows “rows LIMIT” (x-axis) against the chosen metric’s value
(y-axis) for both engines.  It uses the *avg* statistic by default;
change STAT_TO_USE below if you prefer min/median/max.

Author: 2025-06-23
"""

import argparse
import json
import re
from pathlib import Path
from collections import defaultdict

import matplotlib.pyplot as plt

# ---------------------------------------------------------------------------

CUBVEC_DIR = Path("cubvec-bench")
PGVEC_DIR = Path("pgvector-bench")
STAT_TO_USE = "avg"  # set to "min", "max" or "median" if needed

DIMENSIONS = [256, 768, 1536]  # the three plots we want
OUTPUT_TEMPLATE = "plots/plot_dim_{dim}_{metric}.png"

# Regex to capture parts of the filename
# Example: cubvec_10_250000_tbl_256_300000.jsonl
FNAME_RE = re.compile(r"^(cubvec|pgvector)_\d+_(\d+)_tbl_(\d+)_(\d+)\.jsonl$")
# groups                1 engine   2 limit   3 dim    4 rows_total


def load_folder(folder: Path, engine_tag: str, metric: str):
    """
    Scan every *.jsonl file in 'folder' and collect:
        key = (dimension, sql_limit)
        val = metric_value (for STAT_TO_USE)
    Returns a dict mapping key→value.
    """
    results = {}
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
        description="Generate comparison plots for cubvec vs pgvector."
    )
    parser.add_argument("metric", type=str, help='Metric name, e.g. "SELECT TIME"')
    args = parser.parse_args()
    metric = args.metric

    cubvec_data = load_folder(CUBVEC_DIR, "cubvec", metric)
    pgvec_data = load_folder(PGVEC_DIR, "pgvector", metric)

    # Plot per dimension -----------------------------------------------------
    for dim in DIMENSIONS:
        fig, ax = plt.subplots(figsize=(6.4, 4.0))  # default dpi → 640×400

        # Collect x/y for each engine
        limits = sorted(
            {lim for (d, lim) in cubvec_data.keys() if d == dim}
            | {lim for (d, lim) in pgvec_data.keys() if d == dim}
        )

        cub_y = [cubvec_data.get((dim, lim)) for lim in limits]
        pg_y = [pgvec_data.get((dim, lim)) for lim in limits]

        ax.plot(limits, cub_y, marker="o", label="cubvec-bench")
        ax.plot(limits, pg_y, marker="s", label="pgvector-bench")

        ax.set_xlabel("LIMIT (# rows)")
        ax.set_ylabel(f"{metric} – {STAT_TO_USE}")
        ax.set_title(f"{metric} vs LIMIT  (dimension {dim})")
        ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.7)
        ax.legend()

        metric_name = "_".join(metric.split(" "))

        out_file = OUTPUT_TEMPLATE.format(dim=dim, metric=metric_name)
        fig.tight_layout()
        fig.savefig(out_file, dpi=150)
        print(f"✓ Saved {out_file}")

    print("All plots generated.")


if __name__ == "__main__":
    main()
