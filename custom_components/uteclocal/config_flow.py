"""Config flow for U-tec Local Gateway integration."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import async_timeout
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)

DOMAIN = "uteclocal"

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST, default="http://192.168.1.40:8000"): str,
    }
)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for U-tec Local Gateway."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial setup step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST].rstrip("/")

            # Test connection to local gateway health endpoint
            try:
                session = async_get_clientsession(self.hass)
                async with async_timeout.timeout(10):
                    response = await session.get(f"{host}/health")
                    if response.status == 200:
                        # Ensure host is not already configured in Home Assistant
                        await self.async_set_unique_id(host)
                        self._abort_if_unique_id_configured()

                        return self.async_create_entry(
                            title="U-tec Local Gateway",
                            data={CONF_HOST: host},
                        )
                    else:
                        _LOGGER.error(f"Gateway returned HTTP status {response.status}")
                        errors["base"] = "cannot_connect"
            except aiohttp.ClientError as err:
                _LOGGER.error(f"Cannot connect to gateway at {host}: {err}")
                errors["base"] = "cannot_connect"
            except Exception as err:  # pylint: disable=broad-except
                _LOGGER.exception(f"Unexpected exception connecting to gateway: {err}")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
