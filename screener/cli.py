"""``screener`` command line. TRA-21 adds ``run`` and ``backtest``; TRA-24 adds ``load``."""

from __future__ import annotations

from pathlib import Path

import typer

from screener.adapters import fixtures as fx

app = typer.Typer(no_args_is_help=True)


@app.callback()
def main() -> None:
    """AML transaction alert screener."""


@app.command()
def fixtures(out: Path = fx.OUT, seed: int = fx.SEED) -> None:
    """Write the synthetic fixture Parquet (data/fixtures/fixture.parquet) and print its SHA-256."""
    typer.echo(f"{fx.write(out, seed)}  {out}")
