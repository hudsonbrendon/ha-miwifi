from types import SimpleNamespace
from unittest.mock import AsyncMock

from custom_components.ha_miwifi.select import (
    MiWiFiChannelSelect,
    MiWiFiTxPowerSelect,
)
from tests.conftest import make_status


def _coord(**kw):
    base = dict(
        data=make_status(True),
        last_update_success=True,
        client=AsyncMock(),
        channels_24g=["0", "1", "6", "11"],
        channels_5g=["0", "36", "149"],
        async_request_refresh=AsyncMock(),
    )
    base.update(kw)
    return SimpleNamespace(**base)


def _entry():
    return SimpleNamespace(entry_id="e1", title="Casa")


def test_channel_select_options_and_current():
    sel = MiWiFiChannelSelect(_coord(), _entry(), wifi_index=1)
    assert sel.options == ["0", "1", "6", "11"]
    assert sel.current_option == "6"  # make_status channel_24g == 6


def test_channel_select_current_none_when_no_options():
    sel = MiWiFiChannelSelect(_coord(channels_24g=[]), _entry(), wifi_index=1)
    assert sel.options == []
    assert sel.current_option is None


async def test_channel_select_calls_client():
    coord = _coord()
    sel = MiWiFiChannelSelect(coord, _entry(), wifi_index=1)
    await sel.async_select_option("11")
    coord.client.async_set_wifi_channel.assert_awaited_once_with(1, "11")
    coord.async_request_refresh.assert_awaited_once()


def test_txpower_select_options_and_current():
    sel = MiWiFiTxPowerSelect(_coord(), _entry(), wifi_index=2)
    assert sel.options == ["max", "mid", "min"]
    assert sel.current_option == "mid"  # make_status txpwr_5g == "mid"


async def test_txpower_select_calls_client():
    coord = _coord()
    sel = MiWiFiTxPowerSelect(coord, _entry(), wifi_index=1)
    await sel.async_select_option("min")
    coord.client.async_set_wifi_txpwr.assert_awaited_once_with(1, "min")
