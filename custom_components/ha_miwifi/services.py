"""Integration actions: DHCP reservations, blocking, port forwards, DMZ, DDNS."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
    callback,
)
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv
import voluptuous as vol

from .const import (
    ATTR_ENTRY_ID,
    DOMAIN,
    SERVICE_ADD_PORT_FORWARD,
    SERVICE_ADD_RESERVATION,
    SERVICE_BLOCK_DEVICE,
    SERVICE_CLEAR_DMZ,
    SERVICE_DELETE_PORT_FORWARD,
    SERVICE_LUCI_REQUEST,
    SERVICE_REMOVE_RESERVATION,
    SERVICE_RUN_SPEED_TEST,
    SERVICE_SET_DDNS,
    SERVICE_SET_DMZ,
    SERVICE_UNBLOCK_DEVICE,
)
from .coordinator import XiaomiMiWiFiCoordinator

_PORT = vol.All(int, vol.Range(min=1, max=65535))

ENTRY_ONLY_SCHEMA = vol.Schema({vol.Required(ATTR_ENTRY_ID): cv.string})
MAC_SCHEMA = ENTRY_ONLY_SCHEMA.extend({vol.Required("mac"): cv.string})
ADD_RESERVATION_SCHEMA = MAC_SCHEMA.extend(
    {vol.Required("ip"): cv.string, vol.Required("name"): cv.string}
)
LUCI_REQUEST_SCHEMA = ENTRY_ONLY_SCHEMA.extend({vol.Required("path"): cv.string})
ADD_PORT_FORWARD_SCHEMA = ENTRY_ONLY_SCHEMA.extend(
    {
        vol.Required("ip"): cv.string,
        vol.Required("name"): cv.string,
        vol.Required("proto"): vol.All(int, vol.Range(min=1, max=3)),
        vol.Required("source_port"): _PORT,
        vol.Required("dest_port"): _PORT,
    }
)
DELETE_PORT_FORWARD_SCHEMA = ENTRY_ONLY_SCHEMA.extend(
    {vol.Required("source_port"): _PORT}
)
SET_DMZ_SCHEMA = ENTRY_ONLY_SCHEMA.extend({vol.Required("ip"): cv.string})
SET_DDNS_SCHEMA = ENTRY_ONLY_SCHEMA.extend({vol.Required("enabled"): cv.boolean})


def _coordinator(hass: HomeAssistant, call: ServiceCall) -> XiaomiMiWiFiCoordinator:
    """Resolve the loaded coordinator for the entry id in the call."""
    entry_id: str = call.data[ATTR_ENTRY_ID]
    entry = hass.config_entries.async_get_entry(entry_id)
    if (
        entry is None
        or entry.domain != DOMAIN
        or entry.state is not ConfigEntryState.LOADED
    ):
        raise ServiceValidationError(f"Config entry '{entry_id}' not found")
    return entry.runtime_data  # type: ignore[no-any-return]


@callback
def async_setup_services(hass: HomeAssistant) -> None:
    """Register the actions once per Home Assistant instance."""

    def _checked(method: str, error: str, *arg_keys: str) -> Any:
        async def handler(call: ServiceCall) -> None:
            coord = _coordinator(hass, call)
            args = [call.data[k] for k in arg_keys]
            if not await getattr(coord.client, method)(*args):
                raise HomeAssistantError(error)
            await coord.async_request_refresh()

        return handler

    async def _luci_request(call: ServiceCall) -> ServiceResponse:
        coord = _coordinator(hass, call)
        return await coord.client.async_luci_request(call.data["path"])  # type: ignore[no-any-return]

    async def _run_speed_test(call: ServiceCall) -> None:
        coord = _coordinator(hass, call)
        await coord.client.async_run_speed_test()
        await coord.async_request_refresh()

    for name, schema, handler in (
        (
            SERVICE_ADD_RESERVATION,
            ADD_RESERVATION_SCHEMA,
            _checked(
                "async_add_dhcp_reservation",
                "Failed to add the DHCP reservation",
                "mac",
                "ip",
                "name",
            ),
        ),
        (
            SERVICE_REMOVE_RESERVATION,
            MAC_SCHEMA,
            _checked(
                "async_remove_dhcp_reservation",
                "Failed to remove the DHCP reservation",
                "mac",
            ),
        ),
        (
            SERVICE_BLOCK_DEVICE,
            MAC_SCHEMA,
            _checked("async_block_device", "Failed to block the device", "mac"),
        ),
        (
            SERVICE_UNBLOCK_DEVICE,
            MAC_SCHEMA,
            _checked("async_unblock_device", "Failed to unblock the device", "mac"),
        ),
        (SERVICE_RUN_SPEED_TEST, ENTRY_ONLY_SCHEMA, _run_speed_test),
        (
            SERVICE_ADD_PORT_FORWARD,
            ADD_PORT_FORWARD_SCHEMA,
            _checked(
                "async_add_port_forward",
                "Failed to add port forward",
                "ip",
                "name",
                "proto",
                "source_port",
                "dest_port",
            ),
        ),
        (
            SERVICE_DELETE_PORT_FORWARD,
            DELETE_PORT_FORWARD_SCHEMA,
            _checked(
                "async_delete_port_forward",
                "Failed to delete port forward",
                "source_port",
            ),
        ),
        (
            SERVICE_SET_DMZ,
            SET_DMZ_SCHEMA,
            _checked("async_set_dmz", "Failed to set DMZ", "ip"),
        ),
        (
            SERVICE_CLEAR_DMZ,
            ENTRY_ONLY_SCHEMA,
            _checked("async_clear_dmz", "Failed to clear DMZ"),
        ),
        (
            SERVICE_SET_DDNS,
            SET_DDNS_SCHEMA,
            _checked("async_set_ddns", "Failed to set DDNS", "enabled"),
        ),
    ):
        hass.services.async_register(DOMAIN, name, handler, schema)

    hass.services.async_register(
        DOMAIN,
        SERVICE_LUCI_REQUEST,
        _luci_request,
        LUCI_REQUEST_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
