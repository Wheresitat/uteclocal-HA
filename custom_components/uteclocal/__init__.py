"""The U-tec Local Gateway integration."""
from __future__ import annotations

import logging
from datetime import timedelta
import aiohttp
import async_timeout

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

_LOGGER = logging.getLogger(__name__)
PLATFORMS: list[Platform] = [Platform.LOCK, Platform.SENSOR]
SCAN_INTERVAL = timedelta(seconds=30)
DOMAIN = "uteclocal"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up U-tec from a config entry."""
    # Obtain official HA OAuth implementation and attach the current session
    implementation = await config_entry_oauth2_flow.async_get_config_entry_implementation(hass, entry)
    oauth_session = config_entry_oauth2_flow.OAuth2Session(hass, entry, implementation)

    coordinator = UtecDataUpdateCoordinator(hass, entry, oauth_session)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


class UtecDataUpdateCoordinator(DataUpdateCoordinator):
    """Manage fetching U-tec data with automatic OAuth2 refresh."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        oauth_session: config_entry_oauth2_flow.OAuth2Session,
    ) -> None:
        self.entry = entry
        self.oauth_session = oauth_session
        self.host = entry.data.get("host", "").rstrip("/")

        super().__init__(
            hass,
            _LOGGER,
            name="U-tec Integration",
            update_interval=SCAN_INTERVAL,
        )

    async def _async_update_data(self):
        """Fetch data using auto-refreshing OAuth session."""
        # 1. Automatically refresh the access token via HA helper if expired
        try:
            await self.oauth_session.async_ensure_token_valid()
        except aiohttp.ClientResponseError as err:
            if err.status == 400 or err.status == 401:
                # Token revoked or refresh token expired: trigger reauth flow in HA UI
                raise ConfigEntryAuthFailed("U-tec refresh token invalid/expired.") from err
            raise UpdateFailed(f"Token refresh failed due to network issue: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Could not refresh access token: {err}") from err

        # 2. Extract valid token header
        token = self.oauth_session.token["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 3. Execute API Data Requests
        try:
            async with async_timeout.timeout(10):
                url = f"{self.host}/api/devices" if self.host else "https://api.u-tec.com/v1/devices"
                async with self.oauth_session.async_get_clientsession(self.hass).get(
                    url, headers=headers
                ) as response:
                    
                    if response.status in (401, 403):
                        # Force token refresh on next poll cycle rather than unauthorizing immediately
                        _LOGGER.warning("Access token rejected (HTTP %s). Forcing token refresh next cycle.", response.status)
                        raise UpdateFailed("Access token rejected by server.")
                    
                    if response.status != 200:
                        raise UpdateFailed(f"API Error HTTP {response.status}")

                    return await response.json()
        except Exception as err:
            raise UpdateFailed(f"Error fetching data: {err}") from err
