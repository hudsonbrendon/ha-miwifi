"""Config flow for the MiWiFi integration."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlowWithReload,
)
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import format_mac
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo
import voluptuous as vol
from xiaomi_miwifi import (
    MiWiFiAuthError,
    MiWiFiClient,
    MiWiFiConnectionError,
    MiWiFiStatus,
)

from .const import (
    CONF_CONSIDER_HOME,
    CONF_EXCLUDED_MACS,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    DEFAULT_CONSIDER_HOME,
    DEFAULT_NAME,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
)

USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


class XiaomiMiWiFiConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the MiWiFi config flow."""

    VERSION = 1

    _discovered: dict[str, Any]
    _parent_mac: str | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            session = async_get_clientsession(self.hass)
            client = MiWiFiClient(
                user_input[CONF_HOST],
                password=user_input[CONF_PASSWORD],
                session=session,
            )
            try:
                await client.async_login()
                status = await client.async_get_status()
            except MiWiFiAuthError:
                errors["base"] = "invalid_auth"
            except MiWiFiConnectionError:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(format_mac(status.mac))
                self._abort_if_unique_id_configured(
                    updates={CONF_HOST: user_input[CONF_HOST]}
                )
                return self.async_create_entry(
                    title=user_input[CONF_NAME], data=user_input
                )
        return self.async_show_form(
            step_id="user", data_schema=USER_SCHEMA, errors=errors
        )

    async def async_step_dhcp(
        self, discovery_info: DhcpServiceInfo
    ) -> ConfigFlowResult:
        await self.async_set_unique_id(format_mac(discovery_info.macaddress))
        self._abort_if_unique_id_configured(updates={CONF_HOST: discovery_info.ip})
        self._async_abort_entries_match({CONF_HOST: discovery_info.ip})
        self._discovered = {
            CONF_HOST: discovery_info.ip,
            CONF_NAME: discovery_info.hostname or DEFAULT_NAME,
        }
        self._parent_mac = None
        self.context["title_placeholders"] = {"name": self._discovered[CONF_NAME]}
        return await self.async_step_discovery_confirm()

    async def async_step_integration_discovery(
        self, discovery_info: dict[str, Any]
    ) -> ConfigFlowResult:
        host = discovery_info[CONF_HOST]
        self._async_abort_entries_match({CONF_HOST: host})
        self._discovered = {
            CONF_HOST: host,
            CONF_NAME: discovery_info.get("name") or DEFAULT_NAME,
        }
        self._parent_mac = discovery_info.get("parent_mac")
        self.context["title_placeholders"] = {"name": self._discovered[CONF_NAME]}
        return await self.async_step_discovery_confirm()

    def _known_passwords(self) -> list[str]:
        seen: list[str] = []
        for entry in self._async_current_entries():
            pwd = entry.data.get(CONF_PASSWORD)
            if pwd and pwd not in seen:
                seen.append(pwd)
        return seen

    async def _validate(self, host: str, password: str) -> MiWiFiStatus | None:
        """Return MiWiFiStatus on success or None on failure."""
        session = async_get_clientsession(self.hass)
        client = MiWiFiClient(host, password=password, session=session)
        try:
            await client.async_login()
            return await client.async_get_status()
        except MiWiFiAuthError, MiWiFiConnectionError:
            return None

    async def _create_discovered(
        self, password: str, status: MiWiFiStatus
    ) -> ConfigFlowResult:
        await self.async_set_unique_id(format_mac(status.mac))
        self._abort_if_unique_id_configured(
            updates={CONF_HOST: self._discovered[CONF_HOST]}
        )
        return self.async_create_entry(
            title=self._discovered[CONF_NAME],
            data={
                CONF_NAME: self._discovered[CONF_NAME],
                CONF_HOST: self._discovered[CONF_HOST],
                CONF_PASSWORD: password,
            },
        )

    async def async_step_discovery_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is None:
            for pwd in self._known_passwords():
                status = await self._validate(self._discovered[CONF_HOST], pwd)
                if status is not None:
                    return await self._create_discovered(pwd, status)
            return self.async_show_form(
                step_id="discovery_confirm",
                data_schema=vol.Schema({vol.Required(CONF_PASSWORD): str}),
                description_placeholders={"host": self._discovered[CONF_HOST]},
            )
        status = await self._validate(
            self._discovered[CONF_HOST], user_input[CONF_PASSWORD]
        )
        if status is None:
            errors["base"] = "invalid_auth"
            return self.async_show_form(
                step_id="discovery_confirm",
                data_schema=vol.Schema({vol.Required(CONF_PASSWORD): str}),
                description_placeholders={"host": self._discovered[CONF_HOST]},
                errors=errors,
            )
        return await self._create_discovered(user_input[CONF_PASSWORD], status)

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> ConfigFlowResult:
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        reauth_entry = self._get_reauth_entry()
        if user_input is not None:
            session = async_get_clientsession(self.hass)
            client = MiWiFiClient(
                reauth_entry.data[CONF_HOST],
                password=user_input[CONF_PASSWORD],
                session=session,
            )
            try:
                await client.async_login()
            except MiWiFiAuthError:
                errors["base"] = "invalid_auth"
            except MiWiFiConnectionError:
                errors["base"] = "cannot_connect"
            else:
                return self.async_update_reload_and_abort(
                    reauth_entry,
                    data_updates={CONF_PASSWORD: user_input[CONF_PASSWORD]},
                )
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_PASSWORD): str}),
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            session = async_get_clientsession(self.hass)
            client = MiWiFiClient(
                user_input[CONF_HOST],
                password=user_input[CONF_PASSWORD],
                session=session,
            )
            try:
                await client.async_login()
                status = await client.async_get_status()
            except MiWiFiAuthError:
                errors["base"] = "invalid_auth"
            except MiWiFiConnectionError:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(format_mac(status.mac))
                self._abort_if_unique_id_mismatch()
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates={
                        CONF_HOST: user_input[CONF_HOST],
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                    },
                )
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST, default=entry.data[CONF_HOST]): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> XiaomiMiWiFiOptionsFlow:
        """Return the options flow."""
        return XiaomiMiWiFiOptionsFlow()


class XiaomiMiWiFiOptionsFlow(OptionsFlowWithReload):
    """Handle polling options; the entry is reloaded when they change."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        opts = self.config_entry.options
        current = opts.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        schema = vol.Schema(
            {
                vol.Optional(CONF_SCAN_INTERVAL, default=current): vol.All(
                    int, vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL)
                ),
                vol.Optional(
                    CONF_CONSIDER_HOME,
                    default=opts.get(CONF_CONSIDER_HOME, DEFAULT_CONSIDER_HOME),
                ): vol.All(int, vol.Range(min=30, max=1800)),
                vol.Optional(
                    CONF_EXCLUDED_MACS,
                    default=opts.get(CONF_EXCLUDED_MACS, ""),
                ): str,
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
