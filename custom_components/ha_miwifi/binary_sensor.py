"""Binary sensor platform for the MiWiFi integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from xiaomi_miwifi import MiWiFiStatus

from .coordinator import MiWiFiConfigEntry, XiaomiMiWiFiCoordinator
from .entity import XiaomiMiWiFiEntity

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class MiWiFiBinaryDescription(BinarySensorEntityDescription):
    value_fn: Callable[[MiWiFiStatus], bool]


BINARY_SENSOR_DESCRIPTIONS: tuple[MiWiFiBinaryDescription, ...] = (
    MiWiFiBinaryDescription(
        key="wan_link",
        translation_key="wan_link",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        value_fn=lambda s: s.wan_link,
    ),
    MiWiFiBinaryDescription(
        key="led",
        translation_key="led",
        icon="mdi:led-on",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda s: s.led_on,
    ),
    MiWiFiBinaryDescription(
        key="dmz",
        translation_key="dmz",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda s: s.dmz_on,
    ),
    MiWiFiBinaryDescription(
        key="ddns",
        translation_key="ddns",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda s: s.ddns_on,
    ),
    MiWiFiBinaryDescription(
        key="ipv6",
        translation_key="ipv6",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda s: s.ipv6_on,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MiWiFiConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    entities: list[BinarySensorEntity] = [
        MiWiFiBinarySensor(coordinator, entry, desc)
        for desc in BINARY_SENSOR_DESCRIPTIONS
    ]
    async_add_entities(entities)


class MiWiFiBinarySensor(XiaomiMiWiFiEntity, BinarySensorEntity):
    entity_description: MiWiFiBinaryDescription

    def __init__(
        self,
        coordinator: XiaomiMiWiFiCoordinator,
        entry: MiWiFiConfigEntry,
        description: MiWiFiBinaryDescription,
    ) -> None:
        super().__init__(coordinator, entry)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"

    @property
    def is_on(self) -> bool:
        return self.entity_description.value_fn(self.coordinator.data)
