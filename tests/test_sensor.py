from types import SimpleNamespace
from unittest.mock import AsyncMock

from homeassistant.exceptions import HomeAssistantError
import pytest

from custom_components.ha_miwifi.binary_sensor import (
    BINARY_SENSOR_DESCRIPTIONS,
)
from custom_components.ha_miwifi.button import MiWiFiRebootButton
from custom_components.ha_miwifi.sensor import (
    SENSOR_DESCRIPTIONS,
    MiWiFiUptimeSensor,
)
from custom_components.ha_miwifi.switch import (
    RADIO_SWITCHES,
    MiWiFiQosSwitch,
    MiWiFiRadioSwitch,
)
from custom_components.ha_miwifi.update import MiWiFiFirmwareUpdate
from tests.conftest import make_status


def test_sensor_descriptions_cover_expected_keys():
    keys = {d.key for d in SENSOR_DESCRIPTIONS}
    assert keys == {
        "client_count",
        "clients_24g",
        "clients_5g",
        "mesh_node_count",
        "download_speed",
        "upload_speed",
        "wan_ip",
        "wan_download_total",
        "wan_upload_total",
        "wan_max_download",
        "wan_max_upload",
        "wan_type",
        "wan_gateway",
        "channel_24g",
        "channel_5g",
        "firmware_version",
        "mode",
        "ethernet_ports",
        "country_code",
        "speedtest_download",
        "speedtest_upload",
        "wan_dns",
        "port_forwards",
        "dhcp_leasetime",
        "timezone",
    }


def test_sensor_value_fns_read_status():
    status = make_status(True)
    by_key = {d.key: d for d in SENSOR_DESCRIPTIONS}
    assert by_key["client_count"].value_fn(status) == 90
    assert by_key["download_speed"].value_fn(status) == 225
    assert by_key["wan_ip"].value_fn(status) == "100.107.54.94"
    assert by_key["mesh_node_count"].value_fn(status) == 2


def test_new_wan_and_wifi_sensor_value_fns():
    status = make_status(True)
    by_key = {d.key: d for d in SENSOR_DESCRIPTIONS}
    assert by_key["wan_download_total"].value_fn(status) == 123456789
    assert by_key["wan_upload_total"].value_fn(status) == 987654321
    assert by_key["wan_max_download"].value_fn(status) == 11800000
    assert by_key["wan_max_upload"].value_fn(status) == 2400000
    assert by_key["wan_type"].value_fn(status) == "dhcp"
    assert by_key["wan_gateway"].value_fn(status) == "100.107.32.1"
    assert by_key["channel_24g"].value_fn(status) == 6
    assert by_key["channel_5g"].value_fn(status) == 149


def test_mode_and_ethernet_sensor_value_fns():
    status = make_status(True)
    by_key = {d.key: d for d in SENSOR_DESCRIPTIONS}
    assert by_key["mode"].value_fn(status) == "Router"
    assert by_key["ethernet_ports"].value_fn(status) == 1


def test_uptime_sensor_reports_last_boot_timestamp():
    from datetime import UTC, datetime

    status = make_status(True)
    coordinator = SimpleNamespace(
        data=status,
        last_update_success=True,
        client=SimpleNamespace(host="1.2.3.4"),
    )
    entry = SimpleNamespace(entry_id="e1", title="Casa")
    sensor = MiWiFiUptimeSensor(coordinator, entry)
    value = sensor.native_value
    assert isinstance(value, datetime)
    # last boot = now - 90861s; should be in the past
    assert value < datetime.now(UTC)
    assert sensor._attr_unique_id == "e1_wan_uptime"


def test_uptime_sensor_is_stable_across_polls(freezer):
    from datetime import timedelta

    status = make_status(True)
    coordinator = SimpleNamespace(
        data=status,
        last_update_success=True,
        client=SimpleNamespace(host="1.2.3.4"),
    )
    entry = SimpleNamespace(entry_id="e1", title="Casa")
    sensor = MiWiFiUptimeSensor(coordinator, entry)

    # Two polls with the SAME wan_uptime but the clock advanced by a few seconds
    # must collapse to the same minute-quantized timestamp (no per-poll jitter).
    freezer.move_to("2026-06-01 12:00:05+00:00")
    first = sensor.native_value
    freezer.tick(timedelta(seconds=7))
    second = sensor.native_value

    assert first == second
    assert first.second == 0
    assert first.microsecond == 0


def test_binary_sensor_descriptions():
    by_key = {d.key: d for d in BINARY_SENSOR_DESCRIPTIONS}
    assert set(by_key) == {"wan_link", "led", "dmz", "ddns", "ipv6"}
    status = make_status(True)
    assert by_key["wan_link"].value_fn(status) is True
    assert by_key["led"].value_fn(status) is True


def test_ipv6_binary_sensor():
    by_key = {d.key: d for d in BINARY_SENSOR_DESCRIPTIONS}
    assert by_key["ipv6"].value_fn(make_status(True)) is False


def test_firmware_update_entity_reports_versions():
    status = make_status(True)
    coordinator = SimpleNamespace(
        data=status,
        last_update_success=True,
        client=SimpleNamespace(host="1.2.3.4"),
    )
    entry = SimpleNamespace(entry_id="e1", title="Casa")
    entity = MiWiFiFirmwareUpdate(coordinator, entry)
    assert entity.installed_version == "1.0.394"
    assert entity.latest_version == "1.0.400"
    assert entity.release_summary == "Bug fixes and stability improvements."
    assert entity._attr_unique_id == "e1_firmware_update"


def test_firmware_update_entity_latest_falls_back_to_installed():
    status = make_status(True)
    status.rom_latest_version = ""
    coordinator = SimpleNamespace(
        data=status,
        last_update_success=True,
        client=SimpleNamespace(host="1.2.3.4"),
    )
    entry = SimpleNamespace(entry_id="e1", title="Casa")
    entity = MiWiFiFirmwareUpdate(coordinator, entry)
    assert entity.latest_version == "1.0.394"


def test_radio_switch_catalog():
    by_key = {s["key"]: s for s in RADIO_SWITCHES}
    assert set(by_key) == {"wifi_5g", "wifi_24g"}
    assert by_key["wifi_5g"]["ifname"] == "wl0"
    assert by_key["wifi_24g"]["ifname"] == "wl1"


async def test_reboot_button_calls_client(hass):
    coordinator = SimpleNamespace(
        client=AsyncMock(),
        data=make_status(True),
        async_request_refresh=AsyncMock(),
        last_update_success=True,
    )
    coordinator.client.async_reboot.return_value = True
    entry = SimpleNamespace(entry_id="e1", title="Casa")
    button = MiWiFiRebootButton(coordinator, entry)
    await button.async_press()
    coordinator.client.async_reboot.assert_awaited_once()


async def test_reboot_button_raises_on_failure(hass):
    coordinator = SimpleNamespace(
        client=AsyncMock(),
        data=make_status(True),
        async_request_refresh=AsyncMock(),
        last_update_success=True,
    )
    coordinator.client.async_reboot = AsyncMock(return_value=False)
    entry = SimpleNamespace(entry_id="e1", title="Casa")
    button = MiWiFiRebootButton(coordinator, entry)
    with pytest.raises(HomeAssistantError):
        await button.async_press()


async def test_radio_switch_turn_off_raises_on_failure(hass):
    coordinator = SimpleNamespace(
        client=AsyncMock(),
        data=make_status(True),
        async_request_refresh=AsyncMock(),
        last_update_success=True,
    )
    coordinator.client.async_set_wifi_enabled = AsyncMock(return_value=False)
    entry = SimpleNamespace(entry_id="e1", title="Casa")
    switch = MiWiFiRadioSwitch(coordinator, entry, RADIO_SWITCHES[0])
    assert switch._attr_is_on is True
    with pytest.raises(HomeAssistantError):
        await switch.async_turn_off()
    assert switch._attr_is_on is True


def test_v05_sensor_value_fns():
    by_key = {d.key: d for d in SENSOR_DESCRIPTIONS}
    s = make_status(True)
    assert by_key["speedtest_download"].value_fn(s) == 865.28
    assert by_key["speedtest_upload"].value_fn(s) == 1553.92
    assert by_key["wan_dns"].value_fn(s) == "1.1.1.1, 8.8.8.8"
    assert by_key["port_forwards"].value_fn(s) == 2
    assert by_key["dhcp_leasetime"].value_fn(s) == 720
    assert by_key["timezone"].value_fn(s) == "CST-8"


def test_v05_binary_sensor_descriptions():
    from custom_components.ha_miwifi.binary_sensor import BINARY_SENSOR_DESCRIPTIONS

    by_key = {d.key: d for d in BINARY_SENSOR_DESCRIPTIONS}
    s = make_status(True)
    assert by_key["dmz"].value_fn(s) is True
    assert by_key["ddns"].value_fn(s) is False


def test_country_code_sensor():
    by_key = {d.key: d for d in SENSOR_DESCRIPTIONS}
    assert by_key["country_code"].value_fn(make_status(True)) == "CN"


async def test_speed_test_button_calls_client():
    from custom_components.ha_miwifi.button import MiWiFiSpeedTestButton

    coord = SimpleNamespace(
        data=make_status(True),
        last_update_success=True,
        client=AsyncMock(),
        async_request_refresh=AsyncMock(),
    )
    entry = SimpleNamespace(entry_id="e1", title="Casa")
    btn = MiWiFiSpeedTestButton(coord, entry)
    await btn.async_press()
    coord.client.async_run_speed_test.assert_awaited_once()
    coord.async_request_refresh.assert_awaited_once()


async def test_qos_switch_on_off():
    coord = SimpleNamespace(
        data=make_status(True),
        last_update_success=True,
        client=AsyncMock(),
        async_request_refresh=AsyncMock(),
    )
    entry = SimpleNamespace(entry_id="e1", title="Casa")
    sw = MiWiFiQosSwitch(coord, entry)
    assert sw.is_on is True  # make_status qos_on == True
    await sw.async_turn_off()
    coord.client.async_set_qos.assert_awaited_once_with(False)
