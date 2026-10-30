"""Sensor platform for the MiWiFi integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import UnitOfDataRate, UnitOfInformation, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util
from xiaomi_miwifi import MiWiFiStatus

from .coordinator import MiWiFiConfigEntry, XiaomiMiWiFiCoordinator
from .entity import XiaomiMiWiFiEntity

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class MiWiFiSensorDescription(SensorEntityDescription):
    """Sensor description with a value extractor."""

    value_fn: Callable[[MiWiFiStatus], object]


SENSOR_DESCRIPTIONS: tuple[MiWiFiSensorDescription, ...] = (
    MiWiFiSensorDescription(
        key="client_count",
        translation_key="client_count",
        icon="mdi:devices",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda s: s.client_count,
    ),
    MiWiFiSensorDescription(
        key="clients_24g",
        translation_key="clients_24g",
        icon="mdi:wifi",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda s: s.clients_24g,
    ),
    MiWiFiSensorDescription(
        key="clients_5g",
        translation_key="clients_5g",
        icon="mdi:wifi",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda s: s.clients_5g,
    ),
    MiWiFiSensorDescription(
        key="mesh_node_count",
        translation_key="mesh_node_count",
        icon="mdi:access-point-network",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda s: s.mesh_node_count,
    ),
    MiWiFiSensorDescription(
        key="download_speed",
        translation_key="download_speed",
        native_unit_of_measurement=UnitOfDataRate.BYTES_PER_SECOND,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:download",
        value_fn=lambda s: s.download_speed,
    ),
    MiWiFiSensorDescription(
        key="upload_speed",
        translation_key="upload_speed",
        native_unit_of_measurement=UnitOfDataRate.BYTES_PER_SECOND,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:upload",
        value_fn=lambda s: s.upload_speed,
    ),
    MiWiFiSensorDescription(
        key="wan_ip",
        translation_key="wan_ip",
        icon="mdi:ip-network",
        value_fn=lambda s: s.wan_ip,
    ),
    MiWiFiSensorDescription(
        key="wan_download_total",
        translation_key="wan_download_total",
        native_unit_of_measurement=UnitOfInformation.BYTES,
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:download-network",
        value_fn=lambda s: s.wan_download_total,
    ),
    MiWiFiSensorDescription(
        key="wan_upload_total",
        translation_key="wan_upload_total",
        native_unit_of_measurement=UnitOfInformation.BYTES,
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:upload-network",
        value_fn=lambda s: s.wan_upload_total,
    ),
    MiWiFiSensorDescription(
        key="wan_max_download",
        translation_key="wan_max_download",
        native_unit_of_measurement=UnitOfDataRate.BYTES_PER_SECOND,
        icon="mdi:download",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda s: s.wan_max_download,
    ),
    MiWiFiSensorDescription(
        key="wan_max_upload",
        translation_key="wan_max_upload",
        native_unit_of_measurement=UnitOfDataRate.BYTES_PER_SECOND,
        icon="mdi:upload",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda s: s.wan_max_upload,
    ),
    MiWiFiSensorDescription(
        key="wan_type",
        translation_key="wan_type",
        icon="mdi:wan",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda s: s.wan_type,
    ),
    MiWiFiSensorDescription(
        key="wan_gateway",
        translation_key="wan_gateway",
        icon="mdi:router-network",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda s: s.wan_gateway,
    ),
    MiWiFiSensorDescription(
        key="channel_24g",
        translation_key="channel_24g",
        icon="mdi:wifi",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda s: s.channel_24g,
    ),
    MiWiFiSensorDescription(
        key="channel_5g",
        translation_key="channel_5g",
        icon="mdi:wifi",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda s: s.channel_5g,
    ),
    MiWiFiSensorDescription(
        key="firmware_version",
        translation_key="firmware_version",
        icon="mdi:chip",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda s: s.firmware_version,
    ),
    MiWiFiSensorDescription(
        key="mode",
        translation_key="mode",
        icon="mdi:router-wireless-settings",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda s: s.mode_name,
    ),
    MiWiFiSensorDescription(
        key="ethernet_ports",
        translation_key="ethernet_ports",
        icon="mdi:ethernet",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda s: s.lan_ports_active,
    ),
    MiWiFiSensorDescription(
        key="country_code",
        translation_key="country_code",
        icon="mdi:earth",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda s: s.country_code,
    ),
    MiWiFiSensorDescription(
        key="speedtest_download",
        translation_key="speedtest_download",
        native_unit_of_measurement="Mbit/s",
        icon="mdi:download-network",
        value_fn=lambda s: s.speedtest_download,
    ),
    MiWiFiSensorDescription(
        key="speedtest_upload",
        translation_key="speedtest_upload",
        native_unit_of_measurement="Mbit/s",
        icon="mdi:upload-network",
        value_fn=lambda s: s.speedtest_upload,
    ),
    MiWiFiSensorDescription(
        key="wan_dns",
        translation_key="wan_dns",
        icon="mdi:dns",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda s: ", ".join(s.wan_dns),
    ),
    MiWiFiSensorDescription(
        key="port_forwards",
        translation_key="port_forwards",
        icon="mdi:lan-connect",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda s: s.port_forward_count,
    ),
    MiWiFiSensorDescription(
        key="dhcp_leasetime",
        translation_key="dhcp_leasetime",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        icon="mdi:timer-cog-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda s: s.dhcp_leasetime,
    ),
    MiWiFiSensorDescription(
        key="timezone",
        translation_key="timezone",
        icon="mdi:map-clock",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda s: s.timezone,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MiWiFiConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    entities: list[SensorEntity] = [
        MiWiFiSensor(coordinator, entry, desc) for desc in SENSOR_DESCRIPTIONS
    ]
    entities.append(MiWiFiUptimeSensor(coordinator, entry))
    async_add_entities(entities)


class MiWiFiSensor(XiaomiMiWiFiEntity, SensorEntity):
    """A single MiWiFi gateway sensor."""

    entity_description: MiWiFiSensorDescription

    def __init__(
        self,
        coordinator: XiaomiMiWiFiCoordinator,
        entry: MiWiFiConfigEntry,
        description: MiWiFiSensorDescription,
    ) -> None:
        super().__init__(coordinator, entry)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"

    @property
    def native_value(self) -> object:
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def available(self) -> bool:
        return super().available and self.coordinator.data.online


class MiWiFiUptimeSensor(XiaomiMiWiFiEntity, SensorEntity):
    """Reports the WAN last-boot timestamp (now - wan_uptime)."""

    _attr_translation_key = "wan_uptime"
    _attr_icon = "mdi:timer-outline"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: XiaomiMiWiFiCoordinator,
        entry: MiWiFiConfigEntry,
    ) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_wan_uptime"

    @property
    def native_value(self) -> datetime | None:
        uptime = self.coordinator.data.wan_uptime
        if not uptime:
            return None
        raw = dt_util.utcnow() - timedelta(seconds=uptime)
        return raw.replace(second=0, microsecond=0)

    @property
    def available(self) -> bool:
        return super().available and self.coordinator.data.online
