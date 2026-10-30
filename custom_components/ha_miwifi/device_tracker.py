"""Device tracker platform for the MiWiFi integration.

Tracks every client that has ever been seen on the router. Once a MAC has
been observed it keeps its tracker forever: when the device drops off the
network the tracker reports ``not home`` instead of disappearing.
"""

from __future__ import annotations

from homeassistant.components.device_tracker import ScannerEntity, SourceType
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from xiaomi_miwifi import ClientDevice

from .coordinator import MiWiFiConfigEntry, XiaomiMiWiFiCoordinator

PARALLEL_UPDATES = 0


def _signal_quality(signal: int) -> str:
    if signal <= 0:
        return "unknown"
    if signal >= 100:
        return "excellent"
    if signal >= 70:
        return "good"
    if signal >= 40:
        return "weak"
    return "poor"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MiWiFiConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up trackers for known clients and watch for newly-seen MACs."""
    coordinator = entry.runtime_data
    tracked: set[str] = set()

    @callback
    def _add_new_trackers() -> None:
        new_entities: list[MiWiFiDeviceTracker] = []
        for client in coordinator.clients:
            if client.mac in tracked:
                continue
            tracked.add(client.mac)
            new_entities.append(MiWiFiDeviceTracker(coordinator, entry, client.mac))
        if new_entities:
            async_add_entities(new_entities)

    _add_new_trackers()
    entry.async_on_unload(coordinator.async_add_listener(_add_new_trackers))


class MiWiFiDeviceTracker(CoordinatorEntity[XiaomiMiWiFiCoordinator], ScannerEntity):
    """A standalone tracker for a single client MAC seen on the router."""

    _attr_has_entity_name = False

    def __init__(
        self,
        coordinator: XiaomiMiWiFiCoordinator,
        entry: MiWiFiConfigEntry,
        mac: str,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._mac = mac
        self._unique_id = f"{entry.entry_id}_track_{mac}"
        # Cache last-known label/ip so an offline device keeps its name.
        client = self._client()
        self._last_name = client.name if client else mac
        self._last_ip = client.ip if client else None
        self._attr_name = self._last_name

    def _client(self) -> ClientDevice | None:
        for client in self.coordinator.clients:
            if client.mac == self._mac:
                return client
        return None

    @callback
    def _handle_coordinator_update(self) -> None:
        client = self._client()
        if client is not None:
            if client.name:
                self._last_name = client.name
                self._attr_name = client.name
            if client.ip:
                self._last_ip = client.ip
        super()._handle_coordinator_update()

    @property
    def unique_id(self) -> str:
        # ScannerEntity defaults unique_id to the MAC; override so each tracker
        # is namespaced to the config entry per the integration's convention.
        return self._unique_id

    @property
    def is_connected(self) -> bool:
        client = self._client()
        if client is not None and client.online:
            return True
        from homeassistant.util import dt as dt_util

        seen = self.coordinator.last_seen.get(self._mac.upper())
        if seen is None:
            return False
        return (
            dt_util.utcnow() - seen
        ).total_seconds() < self.coordinator.consider_home

    @property
    def source_type(self) -> SourceType:
        return SourceType.ROUTER

    @property
    def ip_address(self) -> str | None:
        client = self._client()
        if client is not None and client.ip:
            return client.ip
        return self._last_ip

    @property
    def mac_address(self) -> str | None:
        return self._mac

    @property
    def hostname(self) -> str | None:
        client = self._client()
        if client is not None and client.name:
            return client.name
        return self._last_name

    @property
    def extra_state_attributes(self) -> dict:
        client = self._client()
        if client is None:
            return {}
        return {
            "signal": client.signal,
            "signal_quality": _signal_quality(client.signal),
            "band": client.band,
            "download_speed": client.download_speed,
            "upload_speed": client.upload_speed,
            "download_total": client.download_total,
            "upload_total": client.upload_total,
            "last_seen": self.coordinator.last_seen.get(self._mac.upper()),
        }
