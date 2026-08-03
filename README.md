# NeelPrajnaPro

A trading-hypothesis research system. `qrf/` is the research/statistics
organ (the "left organ"). `runtime/` — added in a later sprint — will be the
trading organ. A firewall test enforces that neither imports the other's
kernel: `qrf/` never imports `runtime`, and `runtime/` never imports
`qrf.kernel`.

## Requirements

- Python 3.13
- [uv](https://docs.astral.sh/uv/)

## Setup

    uv sync

## Run the test suite

    uv run pytest

## Lint

    uv run ruff check .
