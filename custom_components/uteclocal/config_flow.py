"""Config flow for U-tec integration using OAuth2."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.data_entry_flow import FlowResult

_LOGGER = logging.getLogger(__name__)
DOMAIN = "uteclocal"


class OAuth2FlowHandler(
    config_entry_oauth2_flow.AbstractOAuth2FlowHandler,
    domain=DOMAIN,
):
    """Handle an OAuth2 config flow for U-tec."""

    DOMAIN = DOMAIN
    VERSION = 1

    @property
    def logger(self) -> logging.Logger:
        """Return logger."""
        return _LOGGER

    @property
    def extra_authorize_data(self) -> dict[str, Any]:
        """Extra data needed for authorization."""
        return {"response_type": "code"}

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> FlowResult:
        """Perform re-authentication if tokens are revoked upstream."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm re-authentication."""
        if user_input is not None:
            return await self.async_step_user()

        return self.async_show_form(step_id="reauth_confirm")
