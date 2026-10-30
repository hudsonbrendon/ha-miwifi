from unittest.mock import MagicMock, patch

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry
from xiaomi_miwifi import MiWiFiAuthError

from custom_components.ha_miwifi.const import CONF_SCAN_INTERVAL, DOMAIN
from custom_components.ha_miwifi.diagnostics import async_get_config_entry_diagnostics
from custom_components.ha_miwifi.discovery import async_correlate_and_discover
from tests.conftest import make_status, setup_integration


async def test_setup_and_unload(
    hass: HomeAssistant, mock_client: MagicMock, mock_config_entry: MockConfigEntry
) -> None:
    await setup_integration(hass, mock_config_entry)
    assert mock_config_entry.state is ConfigEntryState.LOADED
    assert mock_config_entry.runtime_data.data.online is True

    device = dr.async_get(hass).async_get_device_by_identifier(
        (DOMAIN, mock_config_entry.entry_id), mock_config_entry.entry_id
    )
    assert device is not None
    assert device.manufacturer == "Xiaomi"
    assert device.sw_version == "1.0.394"
    assert device.serial_number == "SN1"

    state = hass.states.get("sensor.casa_connected_devices")
    assert state is not None and state.state == "90"
    # Router scanner entities stay registry-disabled until the MAC has a device.
    assert er.async_get(hass).async_get_entity_id(
        "device_tracker",
        DOMAIN,
        f"{mock_config_entry.entry_id}_track_AA:BB:CC:DD:EE:01",
    )
    assert hass.states.get("select.casa_2_4_ghz_channel").state == "6"
    assert hass.services.has_service(DOMAIN, "block_device")

    diag = await async_get_config_entry_diagnostics(hass, mock_config_entry)
    assert diag["entry"]["password"] == "**REDACTED**"
    assert diag["status"]["mac"] == "**REDACTED**"
    assert diag["client_count"] == 1

    assert await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_config_entry.state is ConfigEntryState.NOT_LOADED


async def test_setup_auth_error_starts_reauth(
    hass: HomeAssistant, mock_client: MagicMock, mock_config_entry: MockConfigEntry
) -> None:
    mock_client.async_get_status.side_effect = MiWiFiAuthError("bad")
    await setup_integration(hass, mock_config_entry)
    assert mock_config_entry.state is ConfigEntryState.SETUP_ERROR
    assert any(
        flow["context"].get("source") == "reauth"
        for flow in hass.config_entries.flow.async_progress()
    )


async def test_options_change_reloads_entry(
    hass: HomeAssistant, mock_client: MagicMock, mock_config_entry: MockConfigEntry
) -> None:
    await setup_integration(hass, mock_config_entry)
    before = mock_config_entry.runtime_data
    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
    await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_SCAN_INTERVAL: 60}
    )
    await hass.async_block_till_done()
    assert mock_config_entry.state is ConfigEntryState.LOADED
    assert mock_config_entry.runtime_data is not before
    assert mock_config_entry.runtime_data.update_interval.total_seconds() == 60


def _make_device(hass, entry_id, name):
    reg = dr.async_get(hass)
    return reg.async_get_or_create(
        config_entry_id=entry_id, identifiers={(DOMAIN, entry_id)}, name=name
    )


async def test_correlation_links_configured_leaf(hass):
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    gw = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "192.168.31.1"},
        unique_id="28:d1:27:9f:4c:14",
    )
    leaf = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "192.168.31.215"},
        unique_id="8c:de:f9:93:c5:4c",
    )
    gw.add_to_hass(hass)
    leaf.add_to_hass(hass)
    gw_dev = _make_device(hass, gw.entry_id, "Gateway")
    leaf_dev = _make_device(hass, leaf.entry_id, "Leaf")

    status = make_status(True)  # mode 0, mesh_nodes incl. 192.168.31.215
    flows = []
    with patch(
        "custom_components.ha_miwifi.discovery.discovery_flow.async_create_flow",
        side_effect=lambda *a, **k: flows.append(k.get("data")),
    ):
        async_correlate_and_discover(hass, gw, status)

    reg = dr.async_get(hass)
    assert reg.async_get(leaf_dev.id).via_device_id == gw_dev.id
    # .215 is configured -> not discovered; .156 is not -> discovered
    assert any(d[CONF_HOST] == "192.168.31.156" for d in flows)
    assert not any(d[CONF_HOST] == "192.168.31.215" for d in flows)


async def test_correlation_noop_for_leaf_status(hass):
    from dataclasses import replace

    from pytest_homeassistant_custom_component.common import MockConfigEntry

    leaf = MockConfigEntry(domain=DOMAIN, data={CONF_HOST: "192.168.31.215"})
    leaf.add_to_hass(hass)
    status = replace(make_status(True), mode=3)  # not a gateway
    flows = []
    with patch(
        "custom_components.ha_miwifi.discovery.discovery_flow.async_create_flow",
        side_effect=lambda *a, **k: flows.append(1),
    ):
        async_correlate_and_discover(hass, leaf, status)
    assert flows == []


async def test_correlate_and_discover_never_raises(hass):
    """A failure inside discovery/correlation must be swallowed (non-fatal),
    so it can never break async_setup_entry (which would roll back entities)."""
    from unittest.mock import patch

    from pytest_homeassistant_custom_component.common import MockConfigEntry

    from custom_components.ha_miwifi.const import DOMAIN
    from custom_components.ha_miwifi.discovery import async_correlate_and_discover
    from tests.conftest import make_status

    entry = MockConfigEntry(
        domain=DOMAIN, data={CONF_HOST: "192.168.31.1"}, unique_id="28:d1:27:9f:4c:14"
    )
    entry.add_to_hass(hass)
    with patch(
        "custom_components.ha_miwifi.discovery.discovery_flow.async_create_flow",
        side_effect=TypeError("simulated HA API change"),
    ):
        # must NOT raise despite the inner TypeError
        async_correlate_and_discover(hass, entry, make_status(True))
