"""Support for binary_sensor."""

from homeassistant.components.binary_sensor import (
    DOMAIN as ENTITY_DOMAIN,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entities import CatlinkBinaryEntity
from .helpers import Helper


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up CatLink binary sensors from a config entry."""
    hass.data[DOMAIN]["add_entities"][ENTITY_DOMAIN] = async_add_entities
    await Helper.async_setup_accounts(hass, ENTITY_DOMAIN)


async def async_setup_platform(
    hass: HomeAssistant, config, async_add_entities, discovery_info=None
):
    """Set up the Catlink binary_sensor platform via YAML configuration."""
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


class CatlinkBinarySensorEntity(CatlinkBinaryEntity, BinarySensorEntity):
    """BinarySensorEntity."""
