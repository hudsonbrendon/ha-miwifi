"""The MiWiFi integration."""

from __future__ import annotations

import logging

from homeassistant.const import CONF_HOST, Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import format_mac
from homeassistant.helpers.typing import ConfigType
from xiaomi_miwifi import MiWiFiClient

from .const import CONF_PASSWORD, DOMAIN
from .coordinator import MiWiFiConfigEntry, XiaomiMiWiFiCoordinator
from .discovery import async_correlate_and_discover
from .services import async_setup_services

__all__ = ["DOMAIN", "MiWiFiConfigEntry"]

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.DEVICE_TRACKER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.UPDATE,
]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Register the integration-level actions."""
    async_setup_services(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: MiWiFiConfigEntry) -> bool:
    """Set up MiWiFi from a config entry."""
    client = MiWiFiClient(
        entry.data[CONF_HOST],
        password=entry.data[CONF_PASSWORD],
        session=async_get_clientsession(hass),
    )
    coordinator = XiaomiMiWiFiCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()
    await coordinator.async_load_channels()

    if entry.unique_id is None or "." in (entry.unique_id or ""):
        mac = coordinator.data.mac
        if mac:
            try:
                hass.config_entries.async_update_entry(entry, unique_id=format_mac(mac))
            except Exception:
                _LOGGER.warning(
                    "MiWiFi unique_id migration to MAC failed", exc_info=True
                )

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    @callback
    def _mesh_update() -> None:
        async_correlate_and_discover(hass, entry, coordinator.data)

    entry.async_on_unload(coordinator.async_add_listener(_mesh_update))
    _mesh_update()
    return True


async def async_unload_entry(hass: HomeAssistant, entry: MiWiFiConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
