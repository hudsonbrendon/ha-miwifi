"""Select platform for the MiWiFi integration (channels, tx power).

These write WiFi configuration (set_wifi) and RESTART the affected radio —
disruptive by design. Exposed for completeness; never exercised against a
live router in tests.
"""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from xiaomi_miwifi import TXPWR_OPTIONS, WIFI_INDEX_5G, WIFI_INDEX_24G

from .coordinator import MiWiFiConfigEntry, XiaomiMiWiFiCoordinator
from .entity import XiaomiMiWiFiEntity

PARALLEL_UPDATES = 1

_BAND_KEY = {WIFI_INDEX_24G: "24g", WIFI_INDEX_5G: "5g"}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MiWiFiConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    entities: list[SelectEntity] = []
    for idx in (WIFI_INDEX_24G, WIFI_INDEX_5G):
        entities.append(MiWiFiChannelSelect(coordinator, entry, idx))
        entities.append(MiWiFiTxPowerSelect(coordinator, entry, idx))
    async_add_entities(entities)


class MiWiFiChannelSelect(XiaomiMiWiFiEntity, SelectEntity):
    """Select the WiFi channel for one band ("0" = auto). Disruptive."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:wifi-settings"

    def __init__(
        self,
        coordinator: XiaomiMiWiFiCoordinator,
        entry: MiWiFiConfigEntry,
        wifi_index: int,
    ) -> None:
        super().__init__(coordinator, entry)
        self._wifi_index = wifi_index
        self._attr_translation_key = f"channel_{_BAND_KEY[wifi_index]}"
        self._attr_unique_id = f"{entry.entry_id}_channel_{_BAND_KEY[wifi_index]}"

    @property
    def options(self) -> list[str]:
        return (
            self.coordinator.channels_24g
            if self._wifi_index == WIFI_INDEX_24G
            else self.coordinator.channels_5g
        )

    @property
    def current_option(self) -> str | None:
        chan = str(
            self.coordinator.data.channel_24g
            if self._wifi_index == WIFI_INDEX_24G
            else self.coordinator.data.channel_5g
        )
        return chan if chan in self.options else None

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.client.async_set_wifi_channel(self._wifi_index, option)
        await self.coordinator.async_request_refresh()


class MiWiFiTxPowerSelect(XiaomiMiWiFiEntity, SelectEntity):
    """Select the WiFi transmit power for one band (max/mid/min). Disruptive."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:wifi-strength-4"
    _attr_options = list(TXPWR_OPTIONS)

    def __init__(
        self,
        coordinator: XiaomiMiWiFiCoordinator,
        entry: MiWiFiConfigEntry,
        wifi_index: int,
    ) -> None:
        super().__init__(coordinator, entry)
        self._wifi_index = wifi_index
        self._attr_translation_key = f"txpower_{_BAND_KEY[wifi_index]}"
        self._attr_unique_id = f"{entry.entry_id}_txpower_{_BAND_KEY[wifi_index]}"

    @property
    def current_option(self) -> str | None:
        txpwr = (
            self.coordinator.data.txpwr_24g
            if self._wifi_index == WIFI_INDEX_24G
            else self.coordinator.data.txpwr_5g
        )
        return txpwr or None

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.client.async_set_wifi_txpwr(self._wifi_index, option)
        await self.coordinator.async_request_refresh()
