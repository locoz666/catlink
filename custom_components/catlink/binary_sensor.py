"""Support for binary_sensor."""

from homeassistant.components.binary_sensor import (
    DOMAIN as ENTITY_DOMAIN,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entitites import CatlinkBinaryEntity
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
    hass.data[DOMAIN]["add_entities"][ENTITY_DOMAIN] = async_add_entities
    await Helper.async_setup_accounts(hass, ENTITY_DOMAIN)


class CatlinkBinarySensorEntity(CatlinkBinaryEntity, BinarySensorEntity):
    """BinarySensorEntity."""
