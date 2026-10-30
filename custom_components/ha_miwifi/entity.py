"""Base entity for the MiWiFi integration (gateway device)."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import XiaomiMiWiFiCoordinator


class XiaomiMiWiFiEntity(CoordinatorEntity[XiaomiMiWiFiCoordinator]):
    """Common device info for the gateway router."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: XiaomiMiWiFiCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        data = coordinator.data
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer=MANUFACTURER,
            model=data.model if data else "Xiaomi Router",
            sw_version=data.firmware_version if data else None,
            serial_number=data.serial if data else None,
            configuration_url=f"http://{coordinator.client.host}",
        )
