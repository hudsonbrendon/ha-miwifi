"""Diagnostics for the MiWiFi integration."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from .const import CONF_PASSWORD
from .coordinator import MiWiFiConfigEntry

TO_REDACT = {CONF_PASSWORD, "serial", "mac", "wan_ip", "wan_gateway"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: MiWiFiConfigEntry
) -> dict[str, Any]:
    """Return the entry data and the last router status, redacted."""
    coordinator = entry.runtime_data
    return {
        "entry": async_redact_data(dict(entry.data), TO_REDACT),
        "status": async_redact_data(asdict(coordinator.data), TO_REDACT),
        "client_count": len(coordinator.clients),
    }
