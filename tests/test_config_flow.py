from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.ha_miwifi.const import CONF_PASSWORD, DOMAIN
from tests.conftest import make_status


async def test_user_flow_creates_entry(hass: HomeAssistant, aioclient_mock):
    with (
        patch("custom_components.ha_miwifi.config_flow.MiWiFiClient") as mock_client,
        patch(
            "custom_components.ha_miwifi.config_flow.async_get_clientsession",
            MagicMock(),
        ),
        patch(
            "custom_components.ha_miwifi.async_setup_entry",
            AsyncMock(return_value=True),
        ),
    ):
        instance = mock_client.return_value
        instance.async_login = AsyncMock(return_value="tok")
        instance.async_get_status = AsyncMock(return_value=make_status(True))
        instance.async_close = AsyncMock()
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        assert result["type"] == FlowResultType.FORM
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_NAME: "Casa",
                CONF_HOST: "192.168.31.1",
                CONF_PASSWORD: "foco2021",
            },
        )
    assert result2["type"] == FlowResultType.CREATE_ENTRY
    assert result2["data"][CONF_HOST] == "192.168.31.1"


async def test_user_flow_handles_auth_error(hass: HomeAssistant, aioclient_mock):
    from xiaomi_miwifi import MiWiFiAuthError

    with (
        patch("custom_components.ha_miwifi.config_flow.MiWiFiClient") as mock_client,
        patch(
            "custom_components.ha_miwifi.config_flow.async_get_clientsession",
            MagicMock(),
        ),
    ):
        instance = mock_client.return_value
        instance.async_login = AsyncMock(side_effect=MiWiFiAuthError("bad"))
        instance.async_close = AsyncMock()
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_NAME: "Casa",
                CONF_HOST: "192.168.31.1",
                CONF_PASSWORD: "wrong",
            },
        )
    assert result2["type"] == FlowResultType.FORM
    assert result2["errors"] == {"base": "invalid_auth"}


async def test_options_flow_accepts_consider_home_and_excluded_macs(hass):
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    from custom_components.ha_miwifi.const import (
        CONF_CONSIDER_HOME,
        CONF_EXCLUDED_MACS,
        CONF_SCAN_INTERVAL,
    )

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_NAME: "Casa", CONF_HOST: "192.168.31.1", CONF_PASSWORD: "p"},
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == FlowResultType.FORM
    # OptionsFlowWithReload reloads the entry on save; keep setup out of it.
    with patch(
        "custom_components.ha_miwifi.async_setup_entry", AsyncMock(return_value=True)
    ):
        result2 = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {
                CONF_SCAN_INTERVAL: 30,
                CONF_CONSIDER_HOME: 300,
                CONF_EXCLUDED_MACS: "AA:BB:CC:DD:EE:FF",
            },
        )
    assert result2["type"] == FlowResultType.CREATE_ENTRY
    assert result2["data"][CONF_CONSIDER_HOME] == 300
    assert result2["data"][CONF_EXCLUDED_MACS] == "AA:BB:CC:DD:EE:FF"


async def test_reauth_flow_updates_password(hass):
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_NAME: "Casa",
            CONF_HOST: "192.168.31.1",
            CONF_PASSWORD: "old",
        },
    )
    entry.add_to_hass(hass)
    with (
        patch("custom_components.ha_miwifi.config_flow.MiWiFiClient") as mc,
        patch(
            "custom_components.ha_miwifi.config_flow.async_get_clientsession",
            MagicMock(),
        ),
        patch(
            "custom_components.ha_miwifi.async_setup_entry",
            AsyncMock(return_value=True),
        ),
    ):
        inst = mc.return_value
        inst.async_login = AsyncMock(return_value="tok")
        inst.async_close = AsyncMock()
        result = await entry.start_reauth_flow(hass)
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_PASSWORD: "new"}
        )
    assert result2["type"] == FlowResultType.ABORT
    assert result2["reason"] == "reauth_successful"
    assert entry.data[CONF_PASSWORD] == "new"


async def test_reauth_flow_invalid_auth(hass):
    from pytest_homeassistant_custom_component.common import MockConfigEntry
    from xiaomi_miwifi import MiWiFiAuthError

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_NAME: "Casa",
            CONF_HOST: "192.168.31.1",
            CONF_PASSWORD: "old",
        },
    )
    entry.add_to_hass(hass)
    with (
        patch("custom_components.ha_miwifi.config_flow.MiWiFiClient") as mc,
        patch(
            "custom_components.ha_miwifi.config_flow.async_get_clientsession",
            MagicMock(),
        ),
    ):
        inst = mc.return_value
        inst.async_login = AsyncMock(side_effect=MiWiFiAuthError("bad"))
        inst.async_close = AsyncMock()
        result = await entry.start_reauth_flow(hass)
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_PASSWORD: "wrong"}
        )
    assert result2["type"] == FlowResultType.FORM
    assert result2["errors"] == {"base": "invalid_auth"}


async def test_user_flow_sets_mac_unique_id(hass):
    from unittest.mock import AsyncMock, MagicMock, patch

    from homeassistant.const import CONF_HOST, CONF_NAME
    from homeassistant.data_entry_flow import FlowResultType

    from custom_components.ha_miwifi.const import CONF_PASSWORD, DOMAIN
    from tests.conftest import make_status

    with (
        patch("custom_components.ha_miwifi.config_flow.MiWiFiClient") as mc,
        patch(
            "custom_components.ha_miwifi.config_flow.async_get_clientsession",
            MagicMock(),
        ),
        patch(
            "custom_components.ha_miwifi.async_setup_entry",
            AsyncMock(return_value=True),
        ),
    ):
        inst = mc.return_value
        inst.async_login = AsyncMock(return_value="tok")
        inst.async_get_status = AsyncMock(return_value=make_status(True))
        inst.async_close = AsyncMock()
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_NAME: "Casa", CONF_HOST: "192.168.31.1", CONF_PASSWORD: "foco2021"},
        )
    assert result2["type"] == FlowResultType.CREATE_ENTRY
    entry = result2["result"]
    # make_status() mac is "28:D1:27:9F:4C:14" -> normalized lowercase colon form
    assert entry.unique_id == "28:d1:27:9f:4c:14"


async def test_reconfigure_flow_updates_host_and_password(hass):
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="28:d1:27:9f:4c:14",
        data={
            CONF_NAME: "Casa",
            CONF_HOST: "192.168.31.1",
            CONF_PASSWORD: "old",
        },
    )
    entry.add_to_hass(hass)
    with (
        patch("custom_components.ha_miwifi.config_flow.MiWiFiClient") as mc,
        patch(
            "custom_components.ha_miwifi.config_flow.async_get_clientsession",
            MagicMock(),
        ),
        patch(
            "custom_components.ha_miwifi.async_setup_entry",
            AsyncMock(return_value=True),
        ),
    ):
        inst = mc.return_value
        inst.async_login = AsyncMock(return_value="tok")
        inst.async_get_status = AsyncMock(return_value=make_status(True))
        inst.async_close = AsyncMock()
        result = await entry.start_reconfigure_flow(hass)
        assert result["type"] == FlowResultType.FORM
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "192.168.31.2", CONF_PASSWORD: "new"},
        )
    assert result2["type"] == FlowResultType.ABORT
    assert result2["reason"] == "reconfigure_successful"
    assert entry.data[CONF_HOST] == "192.168.31.2"
    assert entry.data[CONF_PASSWORD] == "new"


async def test_reconfigure_flow_keeps_mac_unique_id(hass):
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="28:d1:27:9f:4c:14",
        data={
            CONF_NAME: "Casa",
            CONF_HOST: "192.168.31.1",
            CONF_PASSWORD: "old",
        },
    )
    entry.add_to_hass(hass)
    with (
        patch("custom_components.ha_miwifi.config_flow.MiWiFiClient") as mc,
        patch(
            "custom_components.ha_miwifi.config_flow.async_get_clientsession",
            MagicMock(),
        ),
        patch(
            "custom_components.ha_miwifi.async_setup_entry",
            AsyncMock(return_value=True),
        ),
    ):
        inst = mc.return_value
        inst.async_login = AsyncMock(return_value="tok")
        # same physical router -> same MAC reported by the status call
        inst.async_get_status = AsyncMock(return_value=make_status(True))
        inst.async_close = AsyncMock()
        result = await entry.start_reconfigure_flow(hass)
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "192.168.31.50", CONF_PASSWORD: "new"},
        )
    assert result2["type"] == FlowResultType.ABORT
    assert result2["reason"] == "reconfigure_successful"
    # the MAC-based unique_id must be preserved across reconfigure
    assert entry.unique_id == "28:d1:27:9f:4c:14"
    assert entry.data[CONF_HOST] == "192.168.31.50"
    assert entry.data[CONF_PASSWORD] == "new"


async def test_integration_discovery_reuses_password(hass):
    from homeassistant.config_entries import SOURCE_INTEGRATION_DISCOVERY
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    # an existing gateway entry whose password the leaf can reuse
    MockConfigEntry(
        domain=DOMAIN,
        unique_id="28:d1:27:9f:4c:14",
        data={
            CONF_NAME: "GW",
            CONF_HOST: "192.168.31.1",
            CONF_PASSWORD: "foco2021",
        },
    ).add_to_hass(hass)

    with (
        patch("custom_components.ha_miwifi.config_flow.MiWiFiClient") as mc,
        patch(
            "custom_components.ha_miwifi.config_flow.async_get_clientsession",
            MagicMock(),
        ),
        patch(
            "custom_components.ha_miwifi.async_setup_entry",
            AsyncMock(return_value=True),
        ),
    ):
        inst = mc.return_value
        inst.async_login = AsyncMock(return_value="tok")
        inst.async_get_status = AsyncMock(
            return_value=make_status(True, mac="8c:de:f9:93:c5:4c")
        )
        inst.async_close = AsyncMock()
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_INTEGRATION_DISCOVERY},
            data={
                CONF_HOST: "192.168.31.215",
                "name": "Leaf",
                "hardware": "RM1800",
                "parent_mac": "28:D1:27:9F:4C:14",
            },
        )
    # password was reused -> entry created without prompting
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["result"].data[CONF_HOST] == "192.168.31.215"
    assert result["result"].data[CONF_PASSWORD] == "foco2021"


async def test_dhcp_discovery_starts_flow(hass):
    from types import SimpleNamespace

    from homeassistant.config_entries import SOURCE_DHCP

    # async_step_dhcp is duck-typed on ip/hostname/macaddress, so a lightweight
    # stand-in avoids importing the real DhcpServiceInfo, which pulls in
    # homeassistant.components.dhcp (and aiodhcpwatcher) — not installed in CI.
    info = SimpleNamespace(
        ip="192.168.31.215", hostname="xiaomi-c54c", macaddress="8cdef993c54c"
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_DHCP}, data=info
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "discovery_confirm"
