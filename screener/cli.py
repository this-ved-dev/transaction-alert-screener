"""``screener`` CLI. TRA-21: ``run``; TRA-23: ``backtest``; TRA-24: ``load``."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Annotated

import typer

from screener.adapters import fixtures as fx
from screener.engine import DEFAULT_SQLITE, RuleError, run

app = typer.Typer(no_args_is_help=True)


@app.callback()
def main() -> None:
    """AML transaction alert screener."""


@app.command()
def fixtures(out: Path = fx.OUT, seed: int = fx.SEED) -> None:
    """Write the synthetic fixture Parquet (data/fixtures/fixture.parquet) and print its SHA-256."""
    typer.echo(f"{fx.write(out, seed)}  {out}")


@app.command("run")
def run_cmd(
    day: Annotated[
        str | None, typer.Option("--day", help="Business day to evaluate (YYYY-MM-DD).")
    ] = None,
    since: Annotated[
        str | None,
        typer.Option("--since", help="Incremental watermark: ISO timestamp or 'last'."),
    ] = None,
    reconcile: Annotated[
        bool, typer.Option("--reconcile", help="Nightly full-day pass; requires --day.")
    ] = False,
    store: Annotated[str, typer.Option("--store", help="sqlite | postgres")] = "sqlite",
    sqlite_path: Annotated[
        Path, typer.Option("--sqlite-path", help="SQLite file when --store=sqlite.")
    ] = DEFAULT_SQLITE,
    parquet: Annotated[
        Path, typer.Option("--parquet", help="Canonical entries Parquet to screen.")
    ] = fx.OUT,
) -> None:
    """Run live/shadow rules, upsert hits, write a run manifest."""
    if store not in ("sqlite", "postgres"):
        raise typer.BadParameter("store must be sqlite or postgres")
    if day is None and since is None:
        raise typer.BadParameter("pass --day or --since")
    if day is not None and since is not None:
        raise typer.BadParameter("pass --day or --since, not both")
    asof = date.fromisoformat(day) if day else None
    try:
        manifest = run(
            day=asof,
            since=since,
            reconcile=reconcile,
            store=store,  # type: ignore[arg-type]
            sqlite_path=sqlite_path,
            parquet=parquet,
        )
    except RuleError as e:
        typer.secho(str(e), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from e
    typer.echo(
        f"run_id={manifest['run_id']} mode={manifest['mode']} "
        f"hits={manifest['hit_count']} rules={','.join(manifest['rules_run']) or '(none)'} "
        f"duration_ms={manifest['duration_ms']}"
    )
