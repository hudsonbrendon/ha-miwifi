from unittest.mock import AsyncMock

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry
from xiaomi_miwifi import ClientDevice

from custom_components.ha_miwifi.const import DOMAIN
from custom_components.ha_miwifi.coordinator import (
    XiaomiMiWiFiCoordinator,
)
from tests.conftest import make_status


def _entry(hass: HomeAssistant) -> MockConfigEntry:
    entry = MockConfigEntry(domain=DOMAIN)
    entry.add_to_hass(hass)
    return entry


async def test_coordinator_returns_status(hass: HomeAssistant):
    client = AsyncMock()
    client.async_get_status.return_value = make_status(True)
    client.async_get_clients.return_value = []
    coordinator = XiaomiMiWiFiCoordinator(hass, _entry(hass), client)
    await coordinator.async_refresh()
    assert coordinator.data.online is True
    assert coordinator.data.client_count == 90


async def test_coordinator_loads_available_channels(hass: HomeAssistant):
    from custom_components.ha_miwifi.coordinator import (
        XiaomiMiWiFiCoordinator,
    )
    from tests.conftest import make_status

    client = AsyncMock()
    client.async_get_status.return_value = make_status(True)
    client.async_get_clients.return_value = []
    client.async_get_available_channels.side_effect = lambda idx: (
        ["0", "1", "6", "11"] if idx == 1 else ["0", "36", "149"]
    )
    coordinator = XiaomiMiWiFiCoordinator(hass, _entry(hass), client)
    await coordinator.async_load_channels()
    assert coordinator.channels_24g == ["0", "1", "6", "11"]
    assert coordinator.channels_5g == ["0", "36", "149"]


async def test_coordinator_load_channels_swallows_error(hass: HomeAssistant):
    from xiaomi_miwifi import MiWiFiError

    client = AsyncMock()
    client.async_get_available_channels.side_effect = MiWiFiError("x")
    coordinator = XiaomiMiWiFiCoordinator(hass, _entry(hass), client)
    await coordinator.async_load_channels()
    assert coordinator.channels_24g == []
    assert coordinator.channels_5g == []


async def test_coordinator_offline_is_not_fatal(hass: HomeAssistant):
    from xiaomi_miwifi import MiWiFiConnectionError

    client = AsyncMock()
    client.async_get_status.side_effect = MiWiFiConnectionError("down")
    coordinator = XiaomiMiWiFiCoordinator(hass, _entry(hass), client)
    await coordinator.async_refresh()
    assert coordinator.data.online is False


def _client_dev(mac, name="d", online=True):
    return ClientDevice(
        name=name, mac=mac, ip="192.168.31.9", online=online, parent="", is_router=False
    )


async def test_coordinator_fires_connect_and_new_device_events(hass):
    from custom_components.ha_miwifi.const import (
        EVENT_DEVICE_CONNECTED,
        EVENT_NEW_DEVICE,
    )

    events = []
    hass.bus.async_listen(EVENT_NEW_DEVICE, lambda e: events.append(("new", e.data)))
    hass.bus.async_listen(
        EVENT_DEVICE_CONNECTED, lambda e: events.append(("conn", e.data))
    )

    client = AsyncMock()
    client.async_get_status.return_value = make_status(True)
    client.async_get_clients.return_value = [_client_dev("AA:BB:CC:DD:EE:01")]
    coordinator = XiaomiMiWiFiCoordinator(hass, _entry(hass), client)
    await coordinator.async_refresh()  # first sight -> new + connected
    await hass.async_block_till_done()
    kinds = {k for k, _ in events}
    assert "new" in kinds and "conn" in kinds


async def test_coordinator_fires_disconnect_event(hass):
    from custom_components.ha_miwifi.const import EVENT_DEVICE_DISCONNECTED

    seen = []
    hass.bus.async_listen(EVENT_DEVICE_DISCONNECTED, lambda e: seen.append(e.data))
    client = AsyncMock()
    client.async_get_status.return_value = make_status(True)
    client.async_get_clients.side_effect = [
        [_client_dev("AA:BB:CC:DD:EE:01", name="Living Room TV")],  # online
        [],  # gone
    ]
    coordinator = XiaomiMiWiFiCoordinator(hass, _entry(hass), client)
    await coordinator.async_refresh()
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    match = [d for d in seen if d["mac"] == "AA:BB:CC:DD:EE:01"]
    assert match, "disconnect event not fired"
    assert match[0]["name"] == "Living Room TV"
    assert match[0]["ip"] == "192.168.31.9"
