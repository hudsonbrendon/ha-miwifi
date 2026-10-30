"""Update platform for the MiWiFi integration (info-only firmware)."""

from __future__ import annotations

from homeassistant.components.update import (
    UpdateDeviceClass,
    UpdateEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import MiWiFiConfigEntry, XiaomiMiWiFiCoordinator
from .entity import XiaomiMiWiFiEntity

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MiWiFiConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities([MiWiFiFirmwareUpdate(coordinator, entry)])


class MiWiFiFirmwareUpdate(XiaomiMiWiFiEntity, UpdateEntity):
    """Info-only firmware update entity for the gateway router."""

    _attr_translation_key = "firmware"
    _attr_device_class = UpdateDeviceClass.FIRMWARE

    def __init__(
        self,
        coordinator: XiaomiMiWiFiCoordinator,
        entry: MiWiFiConfigEntry,
    ) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_firmware_update"

    @property
    def installed_version(self) -> str | None:
        return self.coordinator.data.firmware_version

    @property
    def latest_version(self) -> str | None:
        data = self.coordinator.data
        return data.rom_latest_version or data.firmware_version

    @property
    def release_summary(self) -> str | None:
        return self.coordinator.data.rom_changelog or None
