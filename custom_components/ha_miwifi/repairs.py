"""Repair issues for the MiWiFi integration."""

from __future__ import annotations

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import issue_registry as ir
from xiaomi_miwifi import SUPPORTED_ROUTERS, MiWiFiStatus

from .const import DOMAIN


@callback
def async_check_issues(
    hass: HomeAssistant, entry_id: str, data: MiWiFiStatus | None
) -> None:
    """Create or clear repair issues based on the freshly fetched status.

    ``data`` is the status just produced by the coordinator update — it must be
    passed in rather than read from ``coordinator.data``, which is still the
    previous value (None on the first refresh) while the update is running.
    """
    if data is None:
        return

    fw_id = f"firmware_update_available_{entry_id}"
    if data.update_available:
        ir.async_create_issue(
            hass,
            DOMAIN,
            fw_id,
            is_fixable=False,
            severity=ir.IssueSeverity.WARNING,
            translation_key="firmware_update_available",
            translation_placeholders={"version": data.rom_latest_version or "?"},
        )
    else:
        ir.async_delete_issue(hass, DOMAIN, fw_id)

    hw = (data.hardware or "").upper()
    unsup_id = f"unsupported_router_{entry_id}"
    if hw and hw not in SUPPORTED_ROUTERS:
        ir.async_create_issue(
            hass,
            DOMAIN,
            unsup_id,
            is_fixable=False,
            severity=ir.IssueSeverity.WARNING,
            translation_key="unsupported_router",
            translation_placeholders={"hardware": hw},
        )
    else:
        ir.async_delete_issue(hass, DOMAIN, unsup_id)
