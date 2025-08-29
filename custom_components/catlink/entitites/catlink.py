"""The component."""

from homeassistant.components import persistent_notification
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ..const import _LOGGER, DOMAIN
from ..modules.device import Device


class CatlinkEntity(CoordinatorEntity):
    """CatlinkEntity."""

    def __init__(self, name, device: Device, option=None) -> None:
        """Initialize the entity."""
        self.coordinator = device.coordinator
        CoordinatorEntity.__init__(self, self.coordinator)
        self.account = self.coordinator.account
        self._name = name
        self._device = device
        self._option = option or {}
        
        # Enable i18n support
        self._attr_has_entity_name = True
        self._attr_translation_key = name.lower().replace(" ", "_")
        
        # Keep original name as fallback
        self._attr_name = name
        self._attr_device_id = f"{device.type}_{device.mac}"
        self._attr_unique_id = f"{self._attr_device_id}-{name}"
        self._attr_icon = self._option.get("icon")
        self._attr_device_class = self._option.get("class")
        self._attr_unit_of_measurement = self._option.get("unit")
        self._attr_state_class = option.get("state_class")
        
        # Build device information
        device_info = {
            "identifiers": {(DOMAIN, self._attr_device_id)},
            "name": device.name or f"{device.type} {device.mac[-4:] if device.mac else device.id}",
            "manufacturer": "CatLink",
        }
        
        # Add optional device information
        if device.model:
            device_info["model"] = device.model
        if device.detail.get("firmwareVersion"):
            device_info["sw_version"] = device.detail.get("firmwareVersion")
        if device.mac:
            device_info["connections"] = {("mac", device.mac)}
        
        # Set proper configuration URL to avoid API URL being shown
        device_info["configuration_url"] = "https://catlinks.cn/"
            
        self._attr_device_info = DeviceInfo(**device_info)
        
        # Debug logging
        _LOGGER.debug(
            "Creating entity '%s' for device '%s' (ID: %s, MAC: %s)", 
            self._attr_unique_id, 
            device.name, 
            device.id, 
            device.mac
        )

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        await super().async_added_to_hass()
        
        # Debug logging: Entity added to HA
        _LOGGER.debug(
            "Entity '%s' added to Home Assistant with device_info: %s", 
            self.entity_id, 
            self._attr_device_info
        )
        
        self._device.listeners[self.entity_id] = self._handle_coordinator_update
        self._handle_coordinator_update()

    def _handle_coordinator_update(self):
        self.update()
        self.async_write_ha_state()

    def update(self) -> None:
        """Update the entity."""
        if hasattr(self._device, self._name):
            self._attr_state = getattr(self._device, self._name)
            _LOGGER.debug(
                "Entity update: %s", [self.entity_id, self._name, self._attr_state]
            )

        fun = self._option.get("state_attrs")
        if callable(fun):
            self._attr_extra_state_attributes = fun()

    @property
    def state(self) -> str:
        """Return the state of the entity."""
        return self._attr_state

    async def async_request_api(self, api, params=None, method="GET", **kwargs) -> dict:
        """Request API."""
        throw = kwargs.pop("throw", None)
        rdt = await self.account.request(api, params, method, **kwargs)
        if throw:
            persistent_notification.create(
                self.hass,
                f"{rdt}",
                f"Request: {api}",
                f"{DOMAIN}-request",
            )
        return rdt
