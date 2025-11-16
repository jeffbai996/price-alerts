"""
Alert storage module - handles reading/writing alerts to JSON.
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional

# Configuration
ALERTS_FILE = "alerts.json"
CHECK_INTERVAL_SECONDS = 60  # Poll every minute - easily editable


class Alert:
    """Represents a single price alert."""

    def __init__(
        self,
        ticker: str,
        target_price: float,
        alert_type: str,  # "above" or "below"
        alert_id: Optional[str] = None,
        status: str = "active",  # "active", "triggered", "disabled"
        one_time: bool = True,
        created_at: Optional[str] = None,
        last_checked: Optional[str] = None,
        triggered_at: Optional[str] = None
    ):
        # Set attributes first before generating ID (which needs self.ticker)
        self.ticker = ticker.upper()
        self.target_price = float(target_price)
        self.alert_type = alert_type.lower()
        self.status = status
        self.one_time = one_time
        self.created_at = created_at or datetime.now().isoformat()
        self.last_checked = last_checked
        self.triggered_at = triggered_at

        # Generate ID after ticker is set
        self.alert_id = alert_id or self._generate_id()

        # Validate alert type
        if self.alert_type not in ["above", "below"]:
            raise ValueError("alert_type must be 'above' or 'below'")

    def _generate_id(self) -> str:
        """Generate a unique alert ID."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
        return f"{self.ticker}_{timestamp}"

    def to_dict(self) -> Dict:
        """Convert alert to dictionary for JSON serialization."""
        return {
            "alert_id": self.alert_id,
            "ticker": self.ticker,
            "target_price": self.target_price,
            "alert_type": self.alert_type,
            "status": self.status,
            "one_time": self.one_time,
            "created_at": self.created_at,
            "last_checked": self.last_checked,
            "triggered_at": self.triggered_at
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Alert':
        """Create an Alert from a dictionary."""
        return cls(**data)

    def __repr__(self) -> str:
        return f"Alert({self.ticker} {self.alert_type} ${self.target_price:.2f}, status={self.status})"


def load_alerts() -> List[Alert]:
    """Load all alerts from the JSON file."""
    if not os.path.exists(ALERTS_FILE):
        return []

    try:
        with open(ALERTS_FILE, 'r') as f:
            data = json.load(f)
            return [Alert.from_dict(alert_data) for alert_data in data]
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def save_alerts(alerts: List[Alert]) -> None:
    """Save all alerts to the JSON file."""
    with open(ALERTS_FILE, 'w') as f:
        json.dump([alert.to_dict() for alert in alerts], f, indent=2)


def add_alert(alert: Alert) -> None:
    """Add a new alert to the storage."""
    alerts = load_alerts()
    alerts.append(alert)
    save_alerts(alerts)


def remove_alert(alert_id: str) -> bool:
    """Remove an alert by ID. Returns True if found and removed."""
    alerts = load_alerts()
    original_count = len(alerts)
    alerts = [a for a in alerts if a.alert_id != alert_id]

    if len(alerts) < original_count:
        save_alerts(alerts)
        return True
    return False


def get_active_alerts() -> List[Alert]:
    """Get all alerts with 'active' status."""
    alerts = load_alerts()
    return [a for a in alerts if a.status == "active"]


def update_alert(alert: Alert) -> bool:
    """Update an existing alert. Returns True if found and updated."""
    alerts = load_alerts()

    for i, existing_alert in enumerate(alerts):
        if existing_alert.alert_id == alert.alert_id:
            alerts[i] = alert
            save_alerts(alerts)
            return True

    return False
