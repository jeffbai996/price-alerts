"""Unified Typer application for managing and running price alerts."""
from __future__ import annotations

import time
from datetime import datetime
from enum import Enum
from typing import Dict, Iterable, Optional

import typer

from alert_storage import (
    CHECK_INTERVAL_SECONDS,
    Alert,
    add_alert,
    get_active_alerts,
    load_alerts,
    remove_alert,
    update_alert,
)
from price_fetcher import get_current_price

try:
    from plyer import notification
except ImportError:  # pragma: no cover - optional dependency for non-GUI envs
    notification = None  # type: ignore[assignment]

app = typer.Typer(help="Manage and monitor stock price alerts from a single CLI entrypoint.")


class AlertType(str, Enum):
    """Supported alert direction choices."""

    ABOVE = "above"
    BELOW = "below"


class StatusFilter(str, Enum):
    """Valid status filters for the list command."""

    ACTIVE = "active"
    TRIGGERED = "triggered"
    DISABLED = "disabled"
    ALL = "all"


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


def _price_snapshot(tickers: Iterable[str]) -> Dict[str, Optional[float]]:
    """Fetch a current price for each ticker (best-effort)."""
    prices: Dict[str, Optional[float]] = {}
    for ticker in tickers:
        price = get_current_price(ticker)
        if price is None:
            typer.echo(f"Unable to fetch price for {ticker}. Will retry next cycle.")
        prices[ticker] = price
    return prices


def _evaluate_alert(alert: Alert, current_price: float) -> bool:
    """Return True if the alert should fire for the given price."""
    if alert.alert_type == "above":
        return current_price >= alert.target_price
    return current_price <= alert.target_price


def _send_notification(alert: Alert, price: float) -> None:
    """Send a desktop notification if the platform supports it."""
    title = f"Price alert for {alert.ticker}"
    message = (
        f"{alert.ticker} {alert.alert_type} {alert.target_price:.2f}; "
        f"current price {price:.2f}"
    )

    if notification is None:
        typer.echo(
            "Desktop notifications unavailable (plyer not installed or unsupported)."
        )
        return

    try:
        notification.notify(title=title, message=message, timeout=10)
    except Exception as exc:  # pragma: no cover - depends on OS notification layer
        typer.echo(f"Failed to send desktop notification: {exc}")


@app.command("list")
def list_alerts(
    status: StatusFilter = typer.Option(
        StatusFilter.ACTIVE,
        "--status",
        "-s",
        case_sensitive=False,
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
    if status != StatusFilter.ALL:
        alerts = [a for a in alerts if a.status == status.value]

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
    if target_price <= 0:
        raise typer.BadParameter(
            "target_price must be a positive value.", param_hint="target_price"
        )

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
        if target_price <= 0:
            raise typer.BadParameter(
                "target price must be positive when updating.", param_hint="--price"
            )
        alert.target_price = target_price
    if alert_type is not None:
        alert.alert_type = alert_type.value
    if one_time is not None:
        alert.one_time = one_time

    update_alert(alert)
    typer.echo(f"Updated alert {alert.alert_id}.")


@app.command()
def monitor(
    interval: int = typer.Option(
        CHECK_INTERVAL_SECONDS,
        "--interval",
        "-i",
        min=5,
        help="Polling interval in seconds between price checks.",
    ),
    max_iterations: Optional[int] = typer.Option(
        None,
        "--iterations",
        help="Optional number of cycles to run (default infinite).",
    ),
) -> None:
    """Continuously check active alerts and log when they trigger."""
    iteration = 0
    while True:
        iteration += 1
        cycle_started = datetime.now().isoformat(timespec="seconds")
        alerts = get_active_alerts()
        if not alerts:
            typer.echo(f"[{cycle_started}] No active alerts found.")
        else:
            typer.echo(
                f"[{cycle_started}] Checking {len(alerts)} active alert(s)..."
            )
            prices = _price_snapshot({a.ticker for a in alerts})
            triggered_in_cycle = 0
            for alert in alerts:
                price = prices.get(alert.ticker)
                if price is None:
                    continue

                if _evaluate_alert(alert, price):
                    timestamp = datetime.now().isoformat(timespec="seconds")
                    alert.last_checked = timestamp
                    alert.triggered_at = timestamp
                    message = (
                        f"{alert.ticker} hit {price:.2f} "
                        f"(target {alert.alert_type} {alert.target_price:.2f})"
                    )
                    typer.secho(message, fg=typer.colors.GREEN)
                    _send_notification(alert, price)
                    if alert.one_time:
                        alert.status = "triggered"
                    update_alert(alert)
                    triggered_in_cycle += 1

            if triggered_in_cycle == 0:
                typer.echo("No alerts triggered this cycle.")

        if max_iterations is not None and iteration >= max_iterations:
            typer.echo("Monitor exiting after reaching iteration limit.")
            break

        typer.echo(f"Sleeping for {interval} seconds before the next check...")
        time.sleep(interval)


if __name__ == "__main__":
    app()
