async def test_system_health_info(hass):
    from types import SimpleNamespace

    from custom_components.ha_miwifi import system_health as sh
    from tests.conftest import make_status

    coord = SimpleNamespace(
        data=make_status(True),
        last_update_success=True,
        client=SimpleNamespace(host="192.168.31.1"),
    )
    from homeassistant.config_entries import ConfigEntryState
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    entry = MockConfigEntry(domain="ha_miwifi", state=ConfigEntryState.LOADED)
    entry.add_to_hass(hass)
    entry.runtime_data = coord
    info = await sh._system_health_info(hass)
    assert info["devices"] == make_status(True).client_count
    assert info["firmware"] == make_status(True).firmware_version


async def test_system_health_info_no_coordinators(hass):
    from custom_components.ha_miwifi import system_health as sh

    info = await sh._system_health_info(hass)
    assert info == {"routers": 0}
