from types import SimpleNamespace
from unittest.mock import MagicMock

from homeassistant.components.device_tracker import SourceType

from custom_components.ha_miwifi import device_tracker
from custom_components.ha_miwifi.device_tracker import (
    MiWiFiDeviceTracker,
    async_setup_entry,
)
from tests.conftest import make_status


def _client(mac, name, ip, online=True):
    return SimpleNamespace(
        mac=mac, name=name, ip=ip, online=online, parent="", is_router=False
    )


def _entry():
    return SimpleNamespace(entry_id="e1", title="Casa", async_on_unload=lambda fn: None)


def _coordinator(clients):
    coord = SimpleNamespace(
        data=make_status(True),
        clients=list(clients),
        last_update_success=True,
        last_seen={},
        consider_home=180,
    )
    coord._listeners = []

    def _add_listener(cb, ctx=None):
        coord._listeners.append(cb)
        return lambda: coord._listeners.remove(cb)

    coord.async_add_listener = _add_listener
    coord.fire = lambda: [cb() for cb in list(coord._listeners)]
    return coord


def test_tracker_is_connected_and_drops_offline():
    online = _client("AA:BB:CC:DD:EE:01", "Phone", "192.168.31.10", online=True)
    coord = _coordinator([online])
    entry = _entry()

    tracker = MiWiFiDeviceTracker(coord, entry, online.mac)
    assert tracker.is_connected is True
    assert tracker.source_type == SourceType.ROUTER
    assert tracker.ip_address == "192.168.31.10"
    assert tracker.mac_address == "AA:BB:CC:DD:EE:01"
    assert tracker.hostname == "Phone"
    assert tracker.unique_id == "e1_track_AA:BB:CC:DD:EE:01"

    # Device drops out of coordinator.clients entirely -> not connected,
    # but the entity still exists and keeps its last-known label/ip.
    coord.clients = []
    assert tracker.is_connected is False
    assert tracker.hostname == "Phone"
    assert tracker.ip_address == "192.168.31.10"


def test_tracker_offline_flag_reports_not_connected():
    c = _client("AA:BB:CC:DD:EE:02", "Laptop", "192.168.31.11", online=False)
    coord = _coordinator([c])
    entry = _entry()
    tracker = MiWiFiDeviceTracker(coord, entry, c.mac)
    assert tracker.is_connected is False


async def test_setup_adds_trackers_and_incrementally_adds_new_mac(hass):
    c1 = _client("AA:BB:CC:DD:EE:01", "Phone", "192.168.31.10")
    coord = _coordinator([c1])
    entry = _entry()
    entry.runtime_data = coord

    added: list = []
    add_cb = MagicMock(side_effect=lambda ents: added.extend(ents))

    await async_setup_entry(hass, entry, add_cb)

    # Initial known client gets a tracker.
    assert add_cb.call_count == 1
    assert [e.mac_address for e in added] == ["AA:BB:CC:DD:EE:01"]

    # A new MAC appears on a later coordinator update.
    c2 = _client("AA:BB:CC:DD:EE:99", "Tablet", "192.168.31.20")
    coord.clients = [c1, c2]
    coord.fire()

    # The listener fired and added only the new MAC (no duplicate for c1).
    assert add_cb.call_count == 2
    new_macs = [e.mac_address for e in add_cb.call_args[0][0]]
    assert new_macs == ["AA:BB:CC:DD:EE:99"]

    # Firing again with no new MACs does not add anything.
    coord.fire()
    assert add_cb.call_count == 2


def test_tracker_exposes_telemetry_attributes():
    from xiaomi_miwifi import ClientDevice

    dev = ClientDevice(
        name="tv",
        mac="AA:BB:CC:DD:EE:01",
        ip="192.168.31.9",
        online=True,
        parent="",
        is_router=False,
        signal=110,
        band="5G",
        download_speed=1000,
        upload_speed=200,
        download_total=5_000_000,
        upload_total=900_000,
    )
    coordinator = _coordinator([dev])
    entry = _entry()
    tracker = MiWiFiDeviceTracker(coordinator, entry, "AA:BB:CC:DD:EE:01")
    attrs = tracker.extra_state_attributes
    assert attrs["signal"] == 110
    assert attrs["band"] == "5G"
    assert attrs["download_speed"] == 1000
    assert attrs["upload_speed"] == 200
    assert attrs["download_total"] == 5_000_000
    assert attrs["upload_total"] == 900_000


def test_async_setup_entry_module_callable():
    # Guard against accidental rename: the platform exposes async_setup_entry.
    assert callable(device_tracker.async_setup_entry)


def test_tracker_signal_quality_and_last_seen():
    from xiaomi_miwifi import ClientDevice

    from custom_components.ha_miwifi.device_tracker import (
        MiWiFiDeviceTracker,
    )

    dev = ClientDevice(
        name="tv",
        mac="AA:BB:CC:DD:EE:01",
        ip="192.168.31.9",
        online=True,
        parent="",
        is_router=False,
        signal=110,
        band="5G",
    )
    coordinator = _coordinator(clients=[dev])
    tracker = MiWiFiDeviceTracker(coordinator, _entry(), "AA:BB:CC:DD:EE:01")
    attrs = tracker.extra_state_attributes
    assert attrs["signal_quality"] == "excellent"
    assert "last_seen" in attrs
