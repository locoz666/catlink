"""Support for number."""

import asyncio

from homeassistant.components.number import DOMAIN as ENTITY_DOMAIN, NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entities import CatlinkEntity
from .helpers import Helper
from .modules.device import Device


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up CatLink numbers from a config entry."""
    hass.data[DOMAIN]["add_entities"][ENTITY_DOMAIN] = async_add_entities
    await Helper.async_setup_accounts(hass, ENTITY_DOMAIN)


async def async_setup_platform(
    hass: HomeAssistant, config, async_add_entities, discovery_info=None
):
    """Set up the Catlink number platform via YAML configuration."""
    # Check if any accounts have been migrated to config entries
    # If so, skip YAML platform setup to avoid duplicate entities
    domain_data = hass.data.get(DOMAIN, {})
    yaml_config = domain_data.get("config", {})
    
    # Get list of YAML accounts
    yaml_accounts = yaml_config.get("accounts") or []
    if "password" in yaml_config:
        single_account = {**yaml_config}
        single_account.pop("accounts", None)
        yaml_accounts.append(single_account)
    
    # Check if all YAML accounts have corresponding config entries
    migrated_count = 0
    for cfg in yaml_accounts:
        if not cfg.get("password"):
            continue
            
        phone = cfg.get("phone")
        phone_iac = cfg.get("phone_iac", "86")
        if not phone:
            continue
            
        unique_id = f"{phone_iac}-{phone}"
        
        # Check if config entry exists for this account
        for entry in hass.config_entries.async_entries(DOMAIN):
            if entry.unique_id == unique_id:
                migrated_count += 1
                break
    
    # If no YAML accounts exist or all have been migrated, skip YAML setup
    if not yaml_accounts or migrated_count == len(yaml_accounts):
        from .const import _LOGGER
        _LOGGER.debug("No YAML accounts or all migrated to config entries, skipping YAML %s platform setup", ENTITY_DOMAIN)
        return
    
    hass.data[DOMAIN]["add_entities"][ENTITY_DOMAIN] = async_add_entities
    await Helper.async_setup_accounts(hass, ENTITY_DOMAIN)


class CatlinkNumberEntity(CatlinkEntity, NumberEntity):
    """NumberEntity."""

    def __init__(self, name, device: Device, option=None) -> None:
        """Initialize the entity."""
        super().__init__(name, device, option)
        self._attr_native_min_value = self._option.get("min", 1)
        self._attr_native_max_value = self._option.get("max", 100)
        self._attr_native_step = self._option.get("step", 1)
        self._attr_native_value = None
        
        # Set input box mode for specific entities
        if name in ["food_out_count", "max_daily_food"]:
            self._attr_mode = NumberMode.BOX

    def update(self) -> None:
        """Update the entity."""
        super().update()
        self._attr_native_value = float(self._attr_state) if self._attr_state is not None else None

    async def async_set_native_value(self, value: float) -> None:
        """Set the native value."""
        ret = False
        fun = self._option.get("async_set_value")
        if callable(fun):
            kws = {
                "entity": self,
            }
            ret = await fun(int(value), **kws)
        if ret:
            self._attr_native_value = value
            self.async_write_ha_state()
            if dly := self._option.get("delay_update"):
                await asyncio.sleep(dly)
                self._handle_coordinator_update()
        return ret