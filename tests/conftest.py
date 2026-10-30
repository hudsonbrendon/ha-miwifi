from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.core import HomeAssistant
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
from xiaomi_miwifi import ClientDevice, MeshNode, MiWiFiStatus

from custom_components.ha_miwifi.const import CONF_PASSWORD, DOMAIN

pytest_plugins = ["pytest_homeassistant_custom_component"]

MAC = "28:d1:27:9f:4c:14"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


def make_status(online: bool = True, *, mac: str = "28:D1:27:9F:4C:14") -> MiWiFiStatus:
    return MiWiFiStatus(
        online=online,
        hardware="RM1800",
        firmware_version="1.0.394",
        serial="SN1",
        mac=mac,
        client_count=90,
        mesh_node_count=2,
        clients_24g=69,
        clients_5g=15,
        wan_ip="100.107.54.94",
        wan_gateway="100.107.32.1",
        wan_type="dhcp",
        wan_uptime=90861,
        wan_link=True,
        upload_speed=150,
        download_speed=225,
        update_available=False,
        wan_download_total=123456789,
        wan_upload_total=987654321,
        wan_max_download=11800000,
        wan_max_upload=2400000,
        led_on=True,
        channel_24g=6,
        channel_5g=149,
        encryption_24g="psk2",
        encryption_5g="psk2",
        txpwr_24g="max",
        txpwr_5g="mid",
        country_code="CN",
        qos_on=True,
        rom_changelog="Bug fixes and stability improvements.",
        rom_latest_version="1.0.400",
        mode=0,
        speedtest_download=865.28,
        speedtest_upload=1553.92,
        speedtest_bandwidth=6.76,
        wan_dns=["1.1.1.1", "8.8.8.8"],
        ddns_on=False,
        dmz_on=True,
        dmz_ip="192.168.31.50",
        port_forward_count=2,
        dhcp_leasetime=720,
        dhcp_limit=250,
        dhcp_start=5,
        timezone="CST-8",
        ipv6_on=False,
        lan_ports=[False, True, False],
        mesh_nodes=[
            MeshNode("Leaf1", "192.168.31.215", "RM1800", "s", 8),
            MeshNode("Leaf2", "192.168.31.156", "RA82", "s", 8),
        ],
    )


@pytest.fixture
def mock_client() -> Generator[MagicMock]:
    """MiWiFiClient stub returning the canned status and one client."""
    with (
        patch("custom_components.ha_miwifi.MiWiFiClient") as factory,
        # Mesh leaves in the canned status would otherwise start real
        # integration_discovery flows (and hit the network).
        patch("custom_components.ha_miwifi.discovery.discovery_flow.async_create_flow"),
    ):
        client = factory.return_value
        client.host = "192.168.31.1"
        client.async_get_status = AsyncMock(return_value=make_status(True))
        client.async_get_clients = AsyncMock(
            return_value=[
                ClientDevice(
                    name="Phone",
                    mac="AA:BB:CC:DD:EE:01",
                    ip="192.168.31.10",
                    online=True,
                    parent="",
                    is_router=False,
                )
            ]
        )
        client.async_get_available_channels = AsyncMock(
            side_effect=lambda idx: ["0", "1", "6"] if idx == 1 else ["0", "36"]
        )
        yield client


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    return MockConfigEntry(
        domain=DOMAIN,
        title="Casa",
        unique_id=MAC,
        data={CONF_NAME: "Casa", CONF_HOST: "192.168.31.1", CONF_PASSWORD: "p"},
        entry_id="01JMIWIFIENTRY000000000001",
    )


async def setup_integration(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
