"""DataUpdateCoordinator for the MiWiFi integration."""

from __future__ import annotations

from datetime import datetime, timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util
from xiaomi_miwifi import (
    ClientDevice,
    MiWiFiAuthError,
    MiWiFiClient,
    MiWiFiConnectionError,
    MiWiFiError,
    MiWiFiStatus,
)

from .const import (
    CONF_CONSIDER_HOME,
    CONF_EXCLUDED_MACS,
    CONF_SCAN_INTERVAL,
    DEFAULT_CONSIDER_HOME,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    EVENT_DEVICE_CONNECTED,
    EVENT_DEVICE_DISCONNECTED,
    EVENT_NEW_DEVICE,
)
from .repairs import async_check_issues

_LOGGER = logging.getLogger(__name__)

type MiWiFiConfigEntry = ConfigEntry[XiaomiMiWiFiCoordinator]


class XiaomiMiWiFiCoordinator(DataUpdateCoordinator[MiWiFiStatus]):
    """Polls the MiWiFi router and exposes a MiWiFiStatus to entities."""

    config_entry: MiWiFiConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        entry: MiWiFiConfigEntry,
        client: MiWiFiClient,
    ) -> None:
        """Read the polling options from the entry and bind the client."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(
                seconds=entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
            ),
        )
        self.client = client
        self.clients: list[ClientDevice] = []
        self.channels_24g: list[str] = []
        self.channels_5g: list[str] = []
        self.consider_home: int = entry.options.get(
            CONF_CONSIDER_HOME, DEFAULT_CONSIDER_HOME
        )
        raw_excl: str = entry.options.get(CONF_EXCLUDED_MACS, "")
        self.excluded_macs: set[str] = {
            m.strip().upper() for m in raw_excl.split(",") if m.strip()
        }
        self.last_seen: dict[str, datetime] = {}
        self._known_online: set[str] = set()
        self._known_macs: set[str] = set()
        self._mac_info: dict[str, dict[str, str]] = {}

    async def async_load_channels(self) -> None:
        """Fetch the available channel lists once (they don't change)."""
        try:
            self.channels_24g = await self.client.async_get_available_channels(1)
            self.channels_5g = await self.client.async_get_available_channels(2)
        except MiWiFiError:
            self.channels_24g = []
            self.channels_5g = []

    def _process_device_events(self) -> None:
        now = dt_util.utcnow()
        online_now = {
            c.mac.upper()
            for c in self.clients
            if c.online and c.mac.upper() not in self.excluded_macs
        }
        for c in self.clients:
            mac = c.mac.upper()
            if mac in self.excluded_macs:
                continue
            payload = {"mac": c.mac, "name": c.name, "ip": c.ip}
            self._mac_info[mac] = {"mac": c.mac, "name": c.name, "ip": c.ip}
            if mac not in self._known_macs:
                self._known_macs.add(mac)
                self.hass.bus.async_fire(EVENT_NEW_DEVICE, payload)
            if c.online and mac not in self._known_online:
                self.hass.bus.async_fire(EVENT_DEVICE_CONNECTED, payload)
            if c.online:
                self.last_seen[mac] = now
        for mac in self._known_online - online_now:
            self.hass.bus.async_fire(
                EVENT_DEVICE_DISCONNECTED,
                self._mac_info.get(mac, {"mac": mac}),
            )
        self._known_online = online_now

    async def _async_update_data(self) -> MiWiFiStatus:
        try:
            status = await self.client.async_get_status()
        except MiWiFiAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except MiWiFiConnectionError as err:
            _LOGGER.debug("MiWiFi unreachable: %s", err)
            return MiWiFiStatus(online=False)
        try:
            self.clients = await self.client.async_get_clients()
        except MiWiFiConnectionError as err:
            _LOGGER.debug("MiWiFi client list fetch failed: %s", err)
            self.clients = []
        if status.online:
            self._process_device_events()
            async_check_issues(self.hass, self.config_entry.entry_id, status)
        return status
