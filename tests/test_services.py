from types import SimpleNamespace
from unittest.mock import AsyncMock

from homeassistant.config_entries import ConfigEntryState
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ha_miwifi.const import (
    DOMAIN,
    SERVICE_ADD_PORT_FORWARD,
    SERVICE_BLOCK_DEVICE,
    SERVICE_CLEAR_DMZ,
    SERVICE_DELETE_PORT_FORWARD,
    SERVICE_LUCI_REQUEST,
    SERVICE_RUN_SPEED_TEST,
    SERVICE_SET_DDNS,
    SERVICE_SET_DMZ,
    SERVICE_UNBLOCK_DEVICE,
)
from custom_components.ha_miwifi.services import async_setup_services


def _make_coordinator() -> SimpleNamespace:
    return SimpleNamespace(
        client=AsyncMock(),
        async_request_refresh=AsyncMock(),
    )


def _register(hass, coord) -> None:
    """Expose ``coord`` as the loaded entry 'e1' and register the actions."""
    entry = MockConfigEntry(domain=DOMAIN, entry_id="e1", state=ConfigEntryState.LOADED)
    entry.add_to_hass(hass)
    entry.runtime_data = coord
    async_setup_services(hass)


async def _call(hass, service: str, mac: str = "AA:BB:CC:DD:EE:FF") -> None:
    await hass.services.async_call(
        DOMAIN,
        service,
        {"entry_id": "e1", "mac": mac},
        blocking=True,
    )


async def test_block_device_calls_client(hass):
    coord = _make_coordinator()
    coord.client.async_block_device.return_value = True
    _register(hass, coord)

    await _call(hass, SERVICE_BLOCK_DEVICE)

    coord.client.async_block_device.assert_awaited_once_with("AA:BB:CC:DD:EE:FF")
    coord.async_request_refresh.assert_awaited_once()


async def test_block_device_raises_on_false(hass):
    coord = _make_coordinator()
    coord.client.async_block_device.return_value = False
    _register(hass, coord)

    with pytest.raises(HomeAssistantError):
        await _call(hass, SERVICE_BLOCK_DEVICE)


async def test_unblock_device_calls_client(hass):
    coord = _make_coordinator()
    coord.client.async_unblock_device.return_value = True
    _register(hass, coord)

    await _call(hass, SERVICE_UNBLOCK_DEVICE)

    coord.client.async_unblock_device.assert_awaited_once_with("AA:BB:CC:DD:EE:FF")
    coord.async_request_refresh.assert_awaited_once()


async def test_unblock_device_raises_on_false(hass):
    coord = _make_coordinator()
    coord.client.async_unblock_device.return_value = False
    _register(hass, coord)

    with pytest.raises(HomeAssistantError):
        await _call(hass, SERVICE_UNBLOCK_DEVICE)


async def test_luci_request_service_returns_response(hass):
    coord = _make_coordinator()
    coord.client.async_luci_request = AsyncMock(return_value={"code": 0, "mode": 0})
    _register(hass, coord)

    result = await hass.services.async_call(
        DOMAIN,
        SERVICE_LUCI_REQUEST,
        {"entry_id": "e1", "path": "api/misystem/router_info"},
        blocking=True,
        return_response=True,
    )

    coord.client.async_luci_request.assert_awaited_once_with("api/misystem/router_info")
    assert result["mode"] == 0


async def test_run_speed_test_service(hass):
    coord = _make_coordinator()
    coord.client.async_run_speed_test = AsyncMock(return_value={"download": 1.0})
    _register(hass, coord)

    await hass.services.async_call(
        DOMAIN, SERVICE_RUN_SPEED_TEST, {"entry_id": "e1"}, blocking=True
    )

    coord.client.async_run_speed_test.assert_awaited_once()
    coord.async_request_refresh.assert_awaited_once()


async def test_port_forward_services(hass):
    coord = _make_coordinator()
    coord.client.async_add_port_forward = AsyncMock(return_value=True)
    coord.client.async_delete_port_forward = AsyncMock(return_value=True)
    _register(hass, coord)

    await hass.services.async_call(
        DOMAIN,
        SERVICE_ADD_PORT_FORWARD,
        {
            "entry_id": "e1",
            "ip": "192.168.31.50",
            "name": "web",
            "proto": 1,
            "source_port": 8080,
            "dest_port": 80,
        },
        blocking=True,
    )
    coord.client.async_add_port_forward.assert_awaited_once_with(
        "192.168.31.50", "web", 1, 8080, 80
    )

    await hass.services.async_call(
        DOMAIN,
        SERVICE_DELETE_PORT_FORWARD,
        {"entry_id": "e1", "source_port": 8080},
        blocking=True,
    )
    coord.client.async_delete_port_forward.assert_awaited_once_with(8080)


async def test_add_port_forward_raises_on_false(hass):
    coord = _make_coordinator()
    coord.client.async_add_port_forward = AsyncMock(return_value=False)
    _register(hass, coord)

    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_ADD_PORT_FORWARD,
            {
                "entry_id": "e1",
                "ip": "192.168.31.50",
                "name": "web",
                "proto": 1,
                "source_port": 8080,
                "dest_port": 80,
            },
            blocking=True,
        )


async def test_dmz_and_ddns_services(hass):
    coord = _make_coordinator()
    coord.client.async_set_dmz = AsyncMock(return_value=True)
    coord.client.async_clear_dmz = AsyncMock(return_value=True)
    coord.client.async_set_ddns = AsyncMock(return_value=True)
    _register(hass, coord)

    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_DMZ,
        {"entry_id": "e1", "ip": "192.168.31.50"},
        blocking=True,
    )
    coord.client.async_set_dmz.assert_awaited_once_with("192.168.31.50")

    await hass.services.async_call(
        DOMAIN, SERVICE_CLEAR_DMZ, {"entry_id": "e1"}, blocking=True
    )
    coord.client.async_clear_dmz.assert_awaited_once()

    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_DDNS,
        {"entry_id": "e1", "enabled": True},
        blocking=True,
    )
    coord.client.async_set_ddns.assert_awaited_once_with(True)


async def test_set_dmz_raises_on_false(hass):
    coord = _make_coordinator()
    coord.client.async_set_dmz = AsyncMock(return_value=False)
    _register(hass, coord)

    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET_DMZ,
            {"entry_id": "e1", "ip": "192.168.31.50"},
            blocking=True,
        )


async def test_block_device_unknown_entry_raises(hass):
    coord = _make_coordinator()
    coord.client.async_block_device.return_value = True
    _register(hass, coord)

    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_BLOCK_DEVICE,
            {"entry_id": "nope", "mac": "AA:BB:CC:DD:EE:FF"},
            blocking=True,
        )
