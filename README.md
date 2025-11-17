# Price Alerts

A Typer-based command line tool for creating, managing, and monitoring stock price alerts. Alerts are stored locally in `alerts.json` and evaluated against Yahoo Finance prices fetched via `yfinance`.

## Installation

1. Create and activate a virtual environment (optional but recommended).
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

`plyer` is optional and used only for desktop notifications. The CLI gracefully degrades if it's missing or the host OS doesn't support notifications.

## Managing Alerts

All functionality lives in `app.py`. Use `python app.py --help` to see every available command.

### Listing alerts

```bash
python app.py list --status active --ticker AAPL
```

Supports filtering by status (`active`, `triggered`, `disabled`, `all`) and optionally limiting to a ticker.

### Creating alerts

```bash
python app.py add AAPL 175 above --persistent
```

Each alert gets a unique ID printed after creation. Use the ID with other commands:

```bash
python app.py remove <alert_id>
python app.py enable <alert_id>
python app.py disable <alert_id>
python app.py update <alert_id> --price 180 --type below --persistent
```

All prices must be positive, and `alert_type` must be either `above` or `below`.

## Monitoring Alerts

Start the monitoring loop to continuously evaluate the active alerts against current prices:

```bash
python app.py monitor --interval 15
```

The default interval is 15 seconds, but you can increase it or limit iterations during testing with `--iterations`. The monitor logs each cycle, prints and notifies when alerts fire, and updates alert metadata (`last_checked`, `triggered_at`, `status`). One-time alerts are automatically marked as triggered after they fire.

## Data storage

Alerts are persisted as JSON objects in `alerts.json` at the repository root. You can back up or edit the file manually, but prefer using the CLI commands to avoid corrupting the JSON structure.
