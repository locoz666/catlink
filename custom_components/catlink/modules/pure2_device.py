"""Pure2 water fountain device class for CatLink integration."""

import datetime
from typing import TYPE_CHECKING

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import PERCENTAGE, UnitOfTemperature, UnitOfTime
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from ..const import _LOGGER, DOMAIN
from ..models.additional_cfg import AdditionalDeviceConfig
from .device import Device

if TYPE_CHECKING:
    from .devices_coordinator import DevicesCoordinator


class Pure2Device(Device):
    """Pure2 water fountain device class for CatLink integration."""

    logs: list
    coordinator_logs = None

    def __init__(
        self,
        dat: dict,
        coordinator: "DevicesCoordinator",
        additional_config: AdditionalDeviceConfig = None,
    ) -> None:
        """Initialize the Pure2 device."""
        super().__init__(dat, coordinator, additional_config)

    async def async_init(self) -> None:
        """Initialize the device."""
        await super().async_init()
        self.logs = []
        self.coordinator_logs = DataUpdateCoordinator(
            self.account.hass,
            _LOGGER,
            name=f"{DOMAIN}-{self.id}-logs",
            update_method=self.update_logs,
            update_interval=datetime.timedelta(minutes=1),
        )
        await self.coordinator_logs.async_config_entry_first_refresh()

    async def update_device_detail(self) -> dict:
        """Update device details from API."""
        api = "token/device/purepro/detail"
        pms = {
            "deviceId": self.id,
        }
        rsp = None
        try:
            rsp = await self.account.request(api, pms)
            rdt = rsp.get("data", {}).get("deviceInfo") or {}
        except (TypeError, ValueError) as exc:
            rdt = {}
            _LOGGER.error("Got device detail for %s failed: %s", self.name, exc)
        if not rdt:
            _LOGGER.warning("Got device detail for %s failed: %s", self.name, rsp)
        _LOGGER.debug("Update device detail: %s", rsp)
        self.detail = rdt
        self._handle_listeners()
        return rdt

    async def update_logs(self) -> list:
        """Update the logs of the device."""
        api = "token/device/purepro/stats/log/top5"
        pms = {
            "deviceId": self.id,
        }
        rsp = None
        try:
            rsp = await self.account.request(api, pms)
            rdt = rsp.get("data", {}).get("pureLogTop5") or []
        except (TypeError, ValueError) as exc:
            rdt = {}
            _LOGGER.warning("Got device logs for %s failed: %s", self.name, exc)
        if not rdt:
            _LOGGER.debug("Got device logs for %s failed: %s", self.name, rsp)
        _LOGGER.debug("Update device logs: %s", rsp)
        self.logs = rdt
        self._handle_listeners()
        return rdt

    async def set_run_mode(self, mode: str) -> dict:
        """Set the run mode of the device."""
        api = "token/device/purepro/runMode"
        pms = {
            "deviceId": self.id,
            "runMode": mode,
        }
        rdt = await self.account.request(api, pms, "POST")
        eno = rdt.get("returnCode", 0)
        if eno:
            _LOGGER.error("Set run mode failed: %s", [rdt, pms])
            return False
        await self.update_device_detail()
        _LOGGER.info("Set run mode: %s", [rdt, pms])
        return rdt

    @property
    def state(self) -> str:
        """Return the state of the device."""
        # Map water level status to readable state
        water_level = self.detail.get("waterLevelStrDescription", "")
        run_mode = self.detail.get("runMode", "")
        if water_level:
            return water_level
        return run_mode

    def state_attrs(self) -> dict:
        """Return the state attributes of the device."""
        return {
            "run_mode": self.detail.get("runMode"),
            "water_level_status": self.detail.get("waterLevelStrDescription"),
            "water_level_num_desc": self.detail.get("waterLevelNumDescription"),
            "fluffy_hair_status": self.detail.get("fluffyHairStatus"),
            "pure_light_status": self.detail.get("pureLightStatus"),
            "water_heat_switch": self.detail.get("waterHeatSwitch"),
            "uv_switch": self.detail.get("ultravioletRaysSwitch"),
            "pure_lock_status": self.detail.get("pureLockStatus"),
            "error": self.detail.get("error"),
            "model": self.detail.get("model"),
            "firmware_version": self.detail.get("firmwareVersion"),
        }

    @property
    def water_level(self) -> int:
        """Return the water level percentage."""
        return self.detail.get("waterLevelNum", 0)

    @property
    def filter_countdown(self) -> int:
        """Return the filter element countdown in days."""
        return self.detail.get("filterElementTimeCountdown", 0)

    @property
    def water_temperature(self) -> float:
        """Return the water temperature."""
        return self.detail.get("waterTemperature", 0)

    @property
    def water_quality(self) -> int:
        """Return the water quality value."""
        return self.detail.get("waterQuality", 0)

    @property
    def online(self) -> bool:
        """Return the online status."""
        return self.detail.get("online", False)

    @property
    def uv_light_on(self) -> bool:
        """Return if UV light is on."""
        return self.detail.get("ultravioletRaysSwitch") == "OPEN"

    @property
    def water_heater_on(self) -> bool:
        """Return if water heater is on."""
        return self.detail.get("waterHeatSwitch") == "OPEN"

    @property
    def pure_locked(self) -> bool:
        """Return if device is locked."""
        return self.detail.get("pureLockStatus") == "LOCK"

    @property
    def error(self) -> str:
        """Return the error of the device."""
        error_msg = self.detail.get("currentErrorMessage", "")
        error_type = self.detail.get("currentErrorType", "NONE")
        if error_type != "NONE" and error_msg:
            return error_msg
        return self.detail.get("error", "NORMAL")

    def error_attrs(self) -> dict:
        """Return the error attributes of the device."""
        return {
            "currentErrorMessage": self.detail.get("currentErrorMessage"),
            "currentErrorType": self.detail.get("currentErrorType"),
            "error": self.detail.get("error"),
        }

    @property
    def _last_log(self) -> dict:
        """Return the last log of the device."""
        log = {}
        if self.logs:
            log = self.logs[0] or {}
        return log

    @property
    def last_log(self) -> str:
        """Return the last log of the device."""
        log = self._last_log
        if not log:
            return None
        # Format: "12:32 Cat1 drink, 103s"
        return f"{log.get('time', '')} {log.get('event', '')}".strip()

    def last_log_attrs(self) -> dict:
        """Return the last log attributes of the device."""
        log = self._last_log
        return {
            **log,
            "logs": self.logs,
        }

    @property
    def run_mode(self) -> str:
        """Return the current run mode."""
        return self.detail.get("runMode", "")

    async def select_run_mode(self, mode: str) -> bool:
        """Select run mode for the device."""
        # Mode should already be in API format from the dropdown
        if mode in ["CONTINUOUS_SPRING", "INDUCTION_SPRING", "INTERMITTENT_SPRING"]:
            return await self.set_run_mode(mode)
        
        # Fallback for backward compatibility with friendly names
        mode_map = {
            "continuous_spring": "CONTINUOUS_SPRING",
            "smart_spring": "INDUCTION_SPRING", 
            "intermittent_spring": "INTERMITTENT_SPRING",
        }
        api_mode = mode_map.get(mode.lower().replace(" ", "_"), mode)
        return await self.set_run_mode(api_mode)

    @property
    def hass_sensor(self) -> dict:
        """Return the device sensors."""
        sensors = {
            "state": {
                "icon": "mdi:water",
                "state": self.state,
                "state_attrs": self.state_attrs,
            },
            "water_level": {
                "icon": "mdi:water-percent",
                "state": self.water_level,
                "unit": PERCENTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
            },
            "filter_countdown": {
                "icon": "mdi:calendar-clock",
                "state": self.filter_countdown,
                "unit": UnitOfTime.DAYS,
                "state_class": SensorStateClass.MEASUREMENT,
            },
            "water_quality": {
                "icon": "mdi:water-check",
                "state": self.water_quality,
                "state_class": SensorStateClass.MEASUREMENT,
            },
            "error": {
                "icon": "mdi:alert-circle",
                "state": self.error,
                "state_attrs": self.error_attrs,
            },
            "last_log": {
                "icon": "mdi:cat",
                "state": self.last_log,
                "state_attrs": self.last_log_attrs,
            },
        }
        
        # Add temperature sensor if available (some models may not have it)
        if self.water_temperature > 0:
            sensors["water_temperature"] = {
                "icon": "mdi:thermometer",
                "state": self.water_temperature,
                "unit": UnitOfTemperature.CELSIUS,
                "class": SensorDeviceClass.TEMPERATURE,
                "state_class": SensorStateClass.MEASUREMENT,
            }
        
        return sensors

    @property
    def hass_binary_sensor(self) -> dict:
        """Return the device binary sensors."""
        binary_sensors = {
            "online": {
                "icon": "mdi:wifi",
                "state": self.online,
                "device_class": "connectivity",
            },
            "pure_locked": {
                "icon": "mdi:lock",
                "state": self.pure_locked,
                "device_class": "lock",
            },
        }
        
        # UV light sensor (only for Pure2 UV model)
        if "ultravioletRaysSwitch" in self.detail:
            binary_sensors["uv_light"] = {
                "icon": "mdi:sun-wireless",
                "state": self.uv_light_on,
                "device_class": "light",
            }
        
        # Water heater sensor
        if "waterHeatSwitch" in self.detail:
            binary_sensors["water_heater"] = {
                "icon": "mdi:water-boiler",
                "state": self.water_heater_on,
                "device_class": "heat",
            }
        
        return binary_sensors

    @property
    def hass_select(self) -> dict:
        """Return the device selects."""
        return {
            "run_mode": {
                "icon": "mdi:water-sync",
                "options": ["CONTINUOUS_SPRING", "INDUCTION_SPRING", "INTERMITTENT_SPRING"],
                "current": self.run_mode,
                "async_select": self.select_run_mode,
            }
        }