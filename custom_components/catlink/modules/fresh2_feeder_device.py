"""Fresh2 Feeder device class for CatLink integration."""

import datetime
from typing import TYPE_CHECKING

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import UnitOfMass, UnitOfTime
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from ..const import _LOGGER, DOMAIN
from ..models.additional_cfg import AdditionalDeviceConfig
from .device import Device

if TYPE_CHECKING:
    from .devices_coordinator import DevicesCoordinator


class Fresh2FeederDevice(Device):
    """Fresh2 Feeder device class for CatLink integration."""

    logs: list
    coordinator_logs = None

    def __init__(
        self,
        dat: dict,
        coordinator: "DevicesCoordinator",
        additional_config: AdditionalDeviceConfig = None,
    ) -> None:
        """Initialize the Fresh2 Feeder device."""
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
        api = "token/device/feederpro/detail"
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
        api = "token/device/feederpro/stats/log/top5"
        pms = {
            "deviceId": self.id,
        }
        rsp = None
        try:
            rsp = await self.account.request(api, pms)
            rdt = rsp.get("data", {}).get("feederLogTop5") or []
        except (TypeError, ValueError) as exc:
            rdt = {}
            _LOGGER.warning("Got device logs for %s failed: %s", self.name, exc)
        if not rdt:
            _LOGGER.debug("Got device logs for %s failed: %s", self.name, rsp)
        _LOGGER.debug("Update device logs: %s", rsp)
        self.logs = rdt
        self._handle_listeners()
        return rdt

    @property
    def state(self) -> str:
        """Return the state of the device."""
        # Use bowl balance status or current model
        balance_status = self.detail.get("balanceStatusOfBowl")
        if balance_status == "2":
            return "sufficient"
        elif balance_status == "1":
            return "low"
        elif balance_status == "0":
            return "empty"
        
        # Fallback to model status
        current_model = self.detail.get("currentModel", 0)
        return "smart_mode" if current_model == 0 else "timing_mode"

    def state_attrs(self) -> dict:
        """Return the state attributes of the device."""
        return {
            "current_model": self.detail.get("currentModel"),
            "total_status": self.detail.get("totalStatus"),
            "bowl_status": self.detail.get("bowlStatus"),
            "balance_status_of_bowl": self.detail.get("balanceStatusOfBowl"),
            "real_model": self.detail.get("realModel"),
            "firmware_version": self.detail.get("firmwareVersion"),
            "online": self.detail.get("online"),
        }

    @property
    def bowl_balance(self) -> int:
        """Return the bowl food balance in grams."""
        # weight field represents bowl balance
        weight = self.detail.get("weight")
        try:
            return int(weight) if weight else 0
        except (TypeError, ValueError):
            return 0

    @property
    def total_food_intake(self) -> int:
        """Return today's total food intake in grams."""
        intake = self.detail.get("totalFoodIntake")
        try:
            return int(intake) if intake else 0
        except (TypeError, ValueError):
            return 0

    @property
    def desiccant_countdown(self) -> int:
        """Return desiccant countdown in days."""
        return self.detail.get("desiccantCountdown", 0)

    @property
    def total_balance_desc(self) -> str:
        """Return the total balance description."""
        return self.detail.get("totalBalanceDesc", "")

    @property
    def error(self) -> str:
        """Return the error of the device."""
        error_msg = self.detail.get("currentErrorMessage", "")
        error_type = self.detail.get("currentErrorType", "NONE")
        if error_type != "NONE" and error_msg:
            return error_msg
        return ""

    def error_attrs(self) -> dict:
        """Return the error attributes of the device."""
        return {
            "currentErrorMessage": self.detail.get("currentErrorMessage"),
            "currentErrorType": self.detail.get("currentErrorType"),
            "deviceErrorList": self.detail.get("deviceErrorList", []),
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
        # Format: "16:51 憨憨进食 150s 4g"
        return f"{log.get('time', '')} {log.get('event', '')} {log.get('firstSection', '')} {log.get('secondSection', '')}".strip()

    def last_log_attrs(self) -> dict:
        """Return the last log attributes of the device."""
        log = self._last_log
        return {
            **log,
            "logs": self.logs,
        }

    @property
    def online(self) -> bool:
        """Return the online status."""
        return self.detail.get("online", False)

    @property
    def key_lock_status(self) -> bool:
        """Return if key lock (child lock) is enabled."""
        return self.detail.get("keyLockStatus", False)

    @property
    def indicator_light_on(self) -> bool:
        """Return if indicator light is on."""
        return self.detail.get("indicatorLightStatus") == "OPEN"

    @property
    def night_mode(self) -> bool:
        """Return if night mode is enabled."""
        return self.detail.get("nightModeFlag", False)

    @property
    def battery_installed(self) -> bool:
        """Return if battery is installed."""
        # batteryStatus: 0 = not installed, 1 = installed
        return self.detail.get("batteryStatus", 0) == 1

    @property
    def all_timing_enabled(self) -> bool:
        """Return if all timing is enabled."""
        return self.detail.get("allTimingToggle", False)

    @property
    def error_alert_enabled(self) -> bool:
        """Return if error alert is enabled."""
        return self.detail.get("errorAlertFlag", True)

    @property
    def mode(self) -> str:
        """Return the current mode."""
        current_model = self.detail.get("currentModel", 0)
        return self.modes.get(str(current_model), "unknown")

    @property
    def modes(self) -> dict:
        """Return the device modes."""
        return {
            "0": "Smart Mode",
            "1": "Timing Mode",
        }

    async def select_mode(self, mode, **kwargs) -> bool:
        """Select the device mode."""
        api = "token/device/feederpro/switchMode/v2"
        
        # Find the mode key
        mod = None
        for k, v in self.modes.items():
            if v == mode:
                mod = k
                break
        
        if mod is None:
            _LOGGER.warning("Select mode failed for %s in %s", mode, self.modes)
            return False
        
        # Base parameters
        pms = {
            "deviceId": self.id,
            "feederproRunMode": "00" if mod == "0" else "01",
            "foodOutCount": self.detail.get("autoFillNum", 1),  # Default to 1 portion
        }
        
        # Add smart mode specific parameters
        if mod == "0":  # Smart Mode
            pms["foodBalance"] = self.detail.get("foodBalanceLimit", 10)
            pms["maxFood"] = self.detail.get("maxFoodOutNumber", 2)
        
        rdt = await self.account.request(api, pms, "POST")
        eno = rdt.get("returnCode", 0)
        if eno:
            _LOGGER.error("Select mode failed: %s", [rdt, pms])
            return False
        
        await self.update_device_detail()
        _LOGGER.info("Select mode: %s", [rdt, pms])
        return rdt

    @property
    def food_out_count(self) -> int:
        """Return the food out count per feeding."""
        return self.detail.get("autoFillNum", 1)

    @property
    def max_daily_food(self) -> int:
        """Return the max daily food portions for smart mode."""
        return self.detail.get("maxFoodOutNumber", 2)

    async def set_food_out_count(self, count: int) -> bool:
        """Set the food out count per feeding."""
        api = "token/device/feederpro/switchMode/v2"
        
        current_model = self.detail.get("currentModel", 0)
        pms = {
            "deviceId": self.id,
            "feederproRunMode": "00" if current_model == 0 else "01",
            "foodOutCount": count,
        }
        
        # Add smart mode specific parameters
        if current_model == 0:
            pms["foodBalance"] = self.detail.get("foodBalanceLimit", 10)
            pms["maxFood"] = self.detail.get("maxFoodOutNumber", 2)
        
        rdt = await self.account.request(api, pms, "POST")
        eno = rdt.get("returnCode", 0)
        if eno:
            _LOGGER.error("Set food out count failed: %s", [rdt, pms])
            return False
        
        await self.update_device_detail()
        _LOGGER.info("Set food out count: %s", [rdt, pms])
        return rdt

    async def set_max_daily_food(self, max_food: int) -> bool:
        """Set the max daily food portions for smart mode."""
        # Only applicable in smart mode
        if self.detail.get("currentModel", 0) != 0:
            _LOGGER.warning("Set max daily food only works in smart mode")
            return False
            
        api = "token/device/feederpro/switchMode/v2"
        pms = {
            "deviceId": self.id,
            "feederproRunMode": "00",
            "foodOutCount": self.detail.get("autoFillNum", 1),
            "foodBalance": self.detail.get("foodBalanceLimit", 10),
            "maxFood": max_food,
        }
        
        rdt = await self.account.request(api, pms, "POST")
        eno = rdt.get("returnCode", 0)
        if eno:
            _LOGGER.error("Set max daily food failed: %s", [rdt, pms])
            return False
        
        await self.update_device_detail()
        _LOGGER.info("Set max daily food: %s", [rdt, pms])
        return rdt

    @property
    def hass_sensor(self) -> dict:
        """Return the device sensors."""
        sensors = {
            "state": {
                "icon": "mdi:food",
                "state": self.state,
                "state_attrs": self.state_attrs,
            },
            "bowl_balance": {
                "icon": "mdi:food-variant",
                "state": self.bowl_balance,
                "unit": UnitOfMass.GRAMS,
                "class": SensorDeviceClass.WEIGHT,
                "state_class": SensorStateClass.MEASUREMENT,
            },
            "total_food_intake": {
                "icon": "mdi:food-apple",
                "state": self.total_food_intake,
                "unit": UnitOfMass.GRAMS,
                "state_class": SensorStateClass.TOTAL_INCREASING,
            },
            "desiccant_countdown": {
                "icon": "mdi:water-off",
                "state": self.desiccant_countdown,
                "unit": UnitOfTime.DAYS,
                "state_class": SensorStateClass.MEASUREMENT,
            },
            "total_balance_desc": {
                "icon": "mdi:food-drumstick",
                "state": self.total_balance_desc,
            },
            "last_log": {
                "icon": "mdi:message",
                "state": self.last_log,
                "state_attrs": self.last_log_attrs,
            },
        }
        
        # Only add error sensor if there's an error
        if self.error:
            sensors["error"] = {
                "icon": "mdi:alert-circle",
                "state": self.error,
                "state_attrs": self.error_attrs,
            }
        
        return sensors

    @property
    def hass_binary_sensor(self) -> dict:
        """Return the device binary sensors."""
        return {
            "online": {
                "icon": "mdi:wifi",
                "state": self.online,
                "device_class": "connectivity",
            },
            "key_lock": {
                "icon": "mdi:lock",
                "state": self.key_lock_status,
                "device_class": "lock",
            },
            "indicator_light": {
                "icon": "mdi:led-on",
                "state": self.indicator_light_on,
                "device_class": "light",
            },
            "night_mode": {
                "icon": "mdi:weather-night",
                "state": self.night_mode,
            },
            "battery_installed": {
                "icon": "mdi:battery",
                "state": self.battery_installed,
                "device_class": "battery",
            },
        }

    @property
    def hass_switch(self) -> dict:
        """Return the device switches."""
        return {
            "all_timing": {
                "icon": "mdi:timer",
                "state": self.all_timing_enabled,
                "state_attrs": lambda: {"timings": self.detail.get("timings", [])},
                "async_turn_on": self.async_enable_all_timing,
                "async_turn_off": self.async_disable_all_timing,
            },
            "error_alert": {
                "icon": "mdi:alert",
                "state": self.error_alert_enabled,
                "async_turn_on": self.async_enable_error_alert,
                "async_turn_off": self.async_disable_error_alert,
            },
        }

    async def async_enable_all_timing(self) -> bool:
        """Enable all timing schedules."""
        # This would require a specific API endpoint, placeholder for now
        _LOGGER.info("Enabling all timing for %s", self.name)
        return True

    async def async_disable_all_timing(self) -> bool:
        """Disable all timing schedules."""
        # This would require a specific API endpoint, placeholder for now
        _LOGGER.info("Disabling all timing for %s", self.name)
        return True

    async def async_enable_error_alert(self) -> bool:
        """Enable error alerts."""
        # This would require a specific API endpoint, placeholder for now
        _LOGGER.info("Enabling error alerts for %s", self.name)
        return True

    async def async_disable_error_alert(self) -> bool:
        """Disable error alerts."""
        # This would require a specific API endpoint, placeholder for now
        _LOGGER.info("Disabling error alerts for %s", self.name)
        return True

    @property
    def hass_select(self) -> dict:
        """Return the device selects."""
        selects = {
            "mode": {
                "icon": "mdi:menu",
                "options": list(self.modes.values()),
                "current": self.mode,
                "state_attrs": lambda: {"current_model": self.detail.get("currentModel")},
                "async_select": self.select_mode,
                "delay_update": 5,
                "translation_key": "mode",
            },
        }
        
        return selects

    @property
    def hass_number(self) -> dict:
        """Return the device numbers."""
        numbers = {
            "food_out_count": {
                "icon": "mdi:food",
                "min": 0,
                "max": None,  # No upper limit
                "step": 1,
                "state": self.food_out_count,
                "async_set_value": self.set_food_out_count,
                "delay_update": 3,
            },
        }
        
        # Only add max_daily_food number in smart mode
        if self.detail.get("currentModel", 0) == 0:
            numbers["max_daily_food"] = {
                "icon": "mdi:food-turkey",
                "min": 0,
                "max": None,  # No upper limit
                "step": 1,
                "state": self.max_daily_food,
                "async_set_value": self.set_max_daily_food,
                "delay_update": 3,
            }
        
        return numbers