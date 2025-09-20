"""Helper functions for the CatLink integration."""

from datetime import timedelta
from typing import TYPE_CHECKING

from homeassistant.core import HomeAssistant

from .const import DOMAIN

if TYPE_CHECKING:
    from .modules.devices_coordinator import DevicesCoordinator


class Helper:
    """Helper class for the CatLink integration."""

    @classmethod
    def calculate_update_interval(cls, update_interval_str) -> timedelta:
        """Calculate a :class:`timedelta` for the polling interval.

        The configuration schema accepts either a ``timedelta`` object (from
        YAML validation) or a string in ``HH:MM:SS`` format (from config
        entries).  The previous implementation attempted to run a regular
        expression against the value without checking its type which raises a
        ``TypeError`` when a ``timedelta`` is supplied.  This prevented YAML
        configured users from setting a custom scan interval and effectively
        broke the integration for them.

        Args:
            update_interval_str: ``timedelta`` or ``HH:MM:SS`` string.

        Returns:
            timedelta: The update interval as a timedelta object.
        """

        if isinstance(update_interval_str, timedelta):
            return update_interval_str

        if isinstance(update_interval_str, (int, float)):
            return timedelta(seconds=int(update_interval_str))

        if isinstance(update_interval_str, str):
            candidate = update_interval_str.strip()

            if not candidate:
                return timedelta(minutes=10)

            if candidate.isdigit():
                return timedelta(seconds=int(candidate))

            try:
                hours, minutes, seconds = candidate.split(":")
            except ValueError:
                pass
            else:
                try:
                    return timedelta(
                        hours=int(hours),
                        minutes=int(minutes),
                        seconds=int(seconds),
                    )
                except ValueError:
                    pass

            try:
                return timedelta(seconds=int(float(candidate)))
            except ValueError:
                pass

        return timedelta(minutes=10)

    @classmethod
    async def async_setup_accounts(cls, hass: HomeAssistant, domain) -> None:
        """Set up the accounts."""
        coordinators: list[DevicesCoordinator] = hass.data[DOMAIN][
            "coordinators"
        ].values()
        for coordinator in coordinators:
            for sta in coordinator.data.values():
                await coordinator.update_hass_entities(domain, sta)

    @classmethod
    async def async_setup_entry(
        cls, hass: HomeAssistant, config_entry, async_add_entities
    ) -> None:
        """Set up the Catlink platform from config entry."""
        # This method is no longer needed as platform files directly implement async_setup_entry
        pass
