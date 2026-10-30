"""Radio on/off switches for the MiWiFi integration.

These toggle physical radios — disruptive by design. Exposed per the
integration's full-control goal; never exercised against the live network
in tests.
"""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import MiWiFiConfigEntry, XiaomiMiWiFiCoordinator
from .entity import XiaomiMiWiFiEntity

PARALLEL_UPDATES = 1

RADIO_SWITCHES: tuple[dict, ...] = (
    {"key": "wifi_5g", "ifname": "wl0", "translation_key": "wifi_5g"},
    {"key": "wifi_24g", "ifname": "wl1", "translation_key": "wifi_24g"},
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MiWiFiConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        MiWiFiRadioSwitch(coordinator, entry, spec) for spec in RADIO_SWITCHES
    )
    async_add_entities([MiWiFiQosSwitch(coordinator, entry)])


class MiWiFiRadioSwitch(XiaomiMiWiFiEntity, SwitchEntity):
    """Enable/disable one radio. State is optimistic (no read-back endpoint)."""

    _attr_icon = "mdi:wifi"

    def __init__(
        self,
        coordinator: XiaomiMiWiFiCoordinator,
        entry: MiWiFiConfigEntry,
        spec: dict,
    ) -> None:
        super().__init__(coordinator, entry)
        self._ifname = spec["ifname"]
        self._attr_translation_key = spec["translation_key"]
        self._attr_unique_id = f"{entry.entry_id}_{spec['key']}"
        self._attr_is_on = True

    async def async_turn_on(self, **kwargs: object) -> None:
        if not await self.coordinator.client.async_set_wifi_enabled(self._ifname, True):
            raise HomeAssistantError(f"Failed to enable radio {self._ifname}")
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: object) -> None:
        if not await self.coordinator.client.async_set_wifi_enabled(
            self._ifname, False
        ):
            raise HomeAssistantError(f"Failed to disable radio {self._ifname}")
        self._attr_is_on = False
        self.async_write_ha_state()


class MiWiFiQosSwitch(XiaomiMiWiFiEntity, SwitchEntity):
    """Enable/disable QoS (smart bandwidth limiting)."""

    _attr_translation_key = "qos"
    _attr_icon = "mdi:speedometer"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: XiaomiMiWiFiCoordinator,
        entry: MiWiFiConfigEntry,
    ) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_qos"

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.qos_on

    async def async_turn_on(self, **kwargs: object) -> None:
        if not await self.coordinator.client.async_set_qos(True):
            raise HomeAssistantError("Failed to enable QoS")
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: object) -> None:
        if not await self.coordinator.client.async_set_qos(False):
            raise HomeAssistantError("Failed to disable QoS")
        await self.coordinator.async_request_refresh()
