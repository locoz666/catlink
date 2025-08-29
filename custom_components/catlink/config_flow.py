"""Config flow for CatLink integration."""

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_SCAN_INTERVAL
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import (
    CONF_API_BASE,
    CONF_LANGUAGE,
    CONF_PHONE,
    CONF_PHONE_IAC,
    DOMAIN,
)
from .modules.account import Account


# Server region options
SERVER_REGIONS = {
    "global": "https://app.catlinks.cn/api/",
    "china": "https://app-sh.catlinks.cn/api/",
    "euroamerica": "https://app-usa.catlinks.cn/api/",
    "singapore": "https://app-sgp.catlinks.cn/api/",
}

# Language options
LANGUAGE_OPTIONS = {
    "zh_CN": "简体中文",
    "en_GB": "English",
}


class CatlinkConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for CatLink."""

    VERSION = 1
    MINOR_VERSION = 1

    def __init__(self):
        """Initialize the config flow."""
        self._user_input = {}

    @staticmethod
    def _format_interval(seconds: int) -> str:
        """Format interval seconds to human-readable string."""
        if seconds < 60:
            return f"{seconds} seconds"
        elif seconds < 3600:
            minutes = seconds // 60
            secs = seconds % 60
            if secs:
                return f"{minutes} minutes {secs} seconds"
            return f"{minutes} minutes"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            if minutes:
                return f"{hours} hours {minutes} minutes"
            return f"{hours} hours"

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the initial step - login information."""
        errors = {}

        if user_input is not None:
            self._user_input.update(user_input)
            
            # Validate authentication
            try:
                await self._validate_auth(user_input)
                return await self.async_step_settings()
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:
                errors["base"] = "unknown"

        # Phase 1: Login information
        data_schema = vol.Schema(
            {
                vol.Required(CONF_PHONE): str,
                vol.Required(CONF_PHONE_IAC, default="86"): str,
                vol.Required(CONF_PASSWORD): str,
                vol.Required("server_region", default="china"): vol.In(SERVER_REGIONS.keys()),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    async def async_step_settings(self, user_input=None) -> FlowResult:
        """Handle the settings step."""
        errors = {}

        if user_input is not None:
            self._user_input.update(user_input)
            
            # If user chooses to configure device-specific settings, go to device config
            if user_input.get("configure_devices", False):
                return await self.async_step_device_config()
            else:
                # Go directly to confirmation step
                return await self.async_step_confirm()

        # Phase 2: System settings
        data_schema = vol.Schema(
            {
                vol.Required("scan_interval_seconds", default=60): vol.All(
                    int, vol.Range(min=5)
                ),
                vol.Required(CONF_LANGUAGE, default="zh_CN"): vol.In(LANGUAGE_OPTIONS.keys()),
                vol.Required("configure_devices", default=False): bool,
            }
        )

        return self.async_show_form(
            step_id="settings",
            data_schema=data_schema,
            errors=errors,
        )

    async def async_step_device_config(self, user_input=None) -> FlowResult:
        """Handle device-specific configuration."""
        errors = {}

        if user_input is not None:
            self._user_input.update(user_input)
            return await self.async_step_confirm()

        # Device-specific configuration
        data_schema = vol.Schema(
            {
                vol.Optional("empty_weight", default=0.0): vol.All(
                    vol.Coerce(float), vol.Range(min=0.0, max=10.0)
                ),
                vol.Optional("max_samples_litter", default=24): vol.All(
                    int, vol.Range(min=1, max=100)
                ),
            }
        )

        return self.async_show_form(
            step_id="device_config",
            data_schema=data_schema,
            errors=errors,
        )

    async def async_step_confirm(self, user_input=None) -> FlowResult:
        """Handle the confirmation step."""
        if user_input is not None:
            seconds = self._user_input['scan_interval_seconds']
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            secs = seconds % 60
            
            config_data = {
                CONF_PHONE: self._user_input[CONF_PHONE],
                CONF_PHONE_IAC: self._user_input[CONF_PHONE_IAC],
                CONF_PASSWORD: self._user_input[CONF_PASSWORD],
                CONF_API_BASE: SERVER_REGIONS[self._user_input["server_region"]],
                CONF_LANGUAGE: self._user_input[CONF_LANGUAGE],
                CONF_SCAN_INTERVAL: f"{hours:02d}:{minutes:02d}:{secs:02d}",
            }
            
            if "empty_weight" in self._user_input:
                config_data["empty_weight"] = self._user_input["empty_weight"]
                config_data["max_samples_litter"] = self._user_input["max_samples_litter"]

            unique_id = f"{self._user_input[CONF_PHONE_IAC]}-{self._user_input[CONF_PHONE]}"
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=f"CatLink ({self._user_input[CONF_PHONE]})",
                data=config_data,
            )

        # Phase 3: Confirm configuration
        region_name = {
            "china": "China",
            "us": "United States", 
            "singapore": "Singapore"
        }.get(self._user_input["server_region"], self._user_input["server_region"])
        
        language_name = LANGUAGE_OPTIONS.get(self._user_input[CONF_LANGUAGE])
        
        config_summary = [
            f"Phone: {self._user_input[CONF_PHONE]}",
            f"Country Code: +{self._user_input[CONF_PHONE_IAC]}",
            f"Server Region: {region_name}",
            f"Update Interval: {self._format_interval(self._user_input['scan_interval_seconds'])}",
            f"Language: {language_name}",
        ]
        
        # If device parameters are configured
        if "empty_weight" in self._user_input:
            config_summary.extend([
                f"Empty Litter Box Weight: {self._user_input['empty_weight']} kg",
                f"Litter Sample Count: {self._user_input['max_samples_litter']}",
            ])

        return self.async_show_form(
            step_id="confirm",
            description_placeholders={"config_summary": "\n".join(config_summary)},
        )

    async def _validate_auth(self, user_input):
        """Validate the user authentication."""
        config = {
            CONF_PHONE: user_input[CONF_PHONE],
            CONF_PHONE_IAC: user_input[CONF_PHONE_IAC],
            CONF_PASSWORD: user_input[CONF_PASSWORD],
            CONF_API_BASE: SERVER_REGIONS[user_input["server_region"]],
            CONF_LANGUAGE: "zh_CN",
        }
        
        account = Account(self.hass, config)
        
        success = await account.async_login()
        if not success:
            raise InvalidAuth
        
        return True

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return CatlinkOptionsFlowHandler(config_entry)


class CatlinkOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for CatLink."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            # Convert seconds back to HH:MM:SS format
            seconds = user_input["scan_interval_seconds"]
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            secs = seconds % 60
            user_input[CONF_SCAN_INTERVAL] = f"{hours:02d}:{minutes:02d}:{secs:02d}"
            
            return self.async_create_entry(title="", data=user_input)

        # Get current configuration and convert to seconds
        current_scan_interval = self.config_entry.data.get(CONF_SCAN_INTERVAL, "00:01:00")
        time_parts = current_scan_interval.split(":")
        current_seconds = int(time_parts[0]) * 3600 + int(time_parts[1]) * 60 + int(time_parts[2])
        
        options_schema = vol.Schema(
            {
                vol.Required("scan_interval_seconds", default=current_seconds): vol.All(
                    int, vol.Range(min=5)
                ),
                vol.Required(CONF_LANGUAGE, 
                    default=self.config_entry.data.get(CONF_LANGUAGE, "zh_CN")
                ): vol.In(LANGUAGE_OPTIONS.keys()),
                vol.Optional("empty_weight", 
                    default=self.config_entry.data.get("empty_weight", 0.0)
                ): vol.All(vol.Coerce(float), vol.Range(min=0.0, max=10.0)),
                vol.Optional("max_samples_litter", 
                    default=self.config_entry.data.get("max_samples_litter", 24)
                ): vol.All(int, vol.Range(min=1, max=100)),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=options_schema,
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""