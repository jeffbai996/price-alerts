"""
Command-line interface for managing price alerts.

This module wires alert_storage functionality into a Typer-based CLI so users
can list, add, remove, and toggle alerts without editing JSON manually.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

import typer

from alert_storage import (
    Alert,
    add_alert,
    load_alerts,
    remove_alert,
    update_alert,
)

app = typer.Typer(help="Manage stock price alerts.")


class AlertType(str, Enum):
    """Supported alert direction choices."""

    ABOVE = "above"
    BELOW = "below"


def _find_alert(alert_id: str) -> Optional[Alert]:
    """Return an alert instance for the given ID, if it exists."""
    for alert in load_alerts():
        if alert.alert_id == alert_id:
            return alert
    return None


def _print_alert(alert: Alert) -> None:
    """Render a single alert in a readable format."""
    typer.echo(
        f"{alert.alert_id} | {alert.ticker} {alert.alert_type} "
        f"${alert.target_price:.2f} | status={alert.status} | one_time={alert.one_time}"
    )


@app.command("list")
def list_alerts(
    status: str = typer.Option(
        "active",
        "--status",
        "-s",
        help="Filter alerts by status (active/triggered/disabled/all).",
    ),
    ticker: Optional[str] = typer.Option(
        None,
        "--ticker",
        "-t",
        help="Restrict results to a specific ticker symbol.",
    ),
) -> None:
    """Display stored alerts with optional filters."""
    alerts = load_alerts()
    if status.lower() != "all":
        alerts = [a for a in alerts if a.status == status.lower()]

    if ticker:
        alerts = [a for a in alerts if a.ticker == ticker.upper()]

    if not alerts:
        typer.echo("No alerts found.")
        return

    for alert in alerts:
        _print_alert(alert)


@app.command()
def add(
    ticker: str = typer.Argument(..., help="Ticker symbol, e.g., AAPL."),
    target_price: float = typer.Argument(..., help="Price threshold to watch."),
    alert_type: AlertType = typer.Argument(
        ...,
        help="Direction: above (price rises to threshold) or below.",
    ),
    one_time: bool = typer.Option(
        True,
        "--one-time / --persistent",
        help="Set alert to fire once (default) or keep firing with --persistent.",
    ),
) -> None:
    """Create a new alert."""
    alert = Alert(
        ticker=ticker,
        target_price=target_price,
        alert_type=alert_type.value,
        one_time=one_time,
    )
    add_alert(alert)
    typer.echo(f"Created alert {alert.alert_id} for {alert.ticker}.")


@app.command()
def remove(alert_id: str = typer.Argument(..., help="Alert identifier to remove.")) -> None:
    """Delete an alert by ID."""
    if remove_alert(alert_id):
        typer.echo(f"Removed alert {alert_id}.")
    else:
        typer.echo(f"Alert {alert_id} not found.")


@app.command()
def enable(alert_id: str = typer.Argument(..., help="Alert identifier to enable.")) -> None:
    """Set an alert's status to active."""
    alert = _find_alert(alert_id)
    if not alert:
        typer.echo(f"Alert {alert_id} not found.")
        return

    alert.status = "active"
    update_alert(alert)
    typer.echo(f"Enabled alert {alert.alert_id}.")


@app.command()
def disable(alert_id: str = typer.Argument(..., help="Alert identifier to disable.")) -> None:
    """Set an alert's status to disabled."""
    alert = _find_alert(alert_id)
    if not alert:
        typer.echo(f"Alert {alert_id} not found.")
        return

    alert.status = "disabled"
    update_alert(alert)
    typer.echo(f"Disabled alert {alert.alert_id}.")


@app.command()
def update(
    alert_id: str = typer.Argument(..., help="Target alert identifier."),
    target_price: Optional[float] = typer.Option(
        None, "--price", "-p", help="Update the target price."
    ),
    alert_type: Optional[AlertType] = typer.Option(
        None,
        "--type",
        "-t",
        help="Change alert direction to above/below.",
    ),
    one_time: Optional[bool] = typer.Option(
        None,
        "--one-time / --persistent",
        help="Toggle between single-fire (--one-time) and repeating (--persistent).",
    ),
) -> None:
    """Update alert configuration fields."""
    alert = _find_alert(alert_id)
    if not alert:
        typer.echo(f"Alert {alert_id} not found.")
        return

    if target_price is not None:
        alert.target_price = target_price
    if alert_type is not None:
        alert.alert_type = alert_type.value
    if one_time is not None:
        alert.one_time = one_time

    update_alert(alert)
    typer.echo(f"Updated alert {alert.alert_id}.")


if __name__ == "__main__":
    app()
