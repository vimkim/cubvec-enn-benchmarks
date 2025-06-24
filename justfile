plot-all: plot-fetch plot-total plot-scan

plot-fetch:
    uv run main.py "SELECT FETCH"

plot-scan:
    uv run main.py "SCAN TIME"

plot-total:
    uv run main.py "TOTAL TIME"

ploti-all: ploti-fetch ploti-total ploti-scan

ploti-fetch:
    uv run plot_interactive.py "SELECT FETCH"

ploti-scan:
    uv run plot_interactive.py "SCAN TIME"

ploti-total:
    uv run plot_interactive.py "TOTAL TIME"

serve:
    # uv run -m http.server 8000 -d .
    miniserve .
