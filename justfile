plot-all: plot-fetch plot-total plot-scan

plot-fetch:
    uv run main.py "SELECT FETCH"

plot-scan:
    uv run main.py "SCAN TIME"

plot-total:
    uv run main.py "TOTAL TIME"

serve:
    uv run python -m http.server 8000 -d plots
