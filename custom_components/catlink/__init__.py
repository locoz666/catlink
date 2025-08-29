"""The component."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_DEVICES, CONF_PASSWORD, CONF_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.helpers.discovery import async_load_platform
from homeassistant.helpers.entity_component import EntityComponent

from .const import _LOGGER, CONF_ACCOUNTS, DOMAIN, SCAN_INTERVAL, SUPPORTED_DOMAINS
from .modules.account import Account
from .modules.devices_coordinator import DevicesCoordinator


async def async_setup(hass: HomeAssistant, hass_config: dict) -> bool:
    """Set up the CatLink component via YAML configuration."""
    hass.data.setdefault(DOMAIN, {})
    config = hass_config.get(DOMAIN) or {}
    hass.data[DOMAIN]["config"] = config
    hass.data[DOMAIN].setdefault(CONF_ACCOUNTS, {})
    hass.data[DOMAIN].setdefault(CONF_DEVICES, {})
    hass.data[DOMAIN].setdefault("coordinators", {})
    hass.data[DOMAIN].setdefault("add_entities", {})

    # If no config or only config entry exists, skip YAML setup
    if not config or len(config) == 0:
        return True

    component = EntityComponent(_LOGGER, DOMAIN, hass, SCAN_INTERVAL)
    hass.data[DOMAIN]["component"] = component
    await component.async_setup(config)

    als = config.get(CONF_ACCOUNTS) or []
    if CONF_PASSWORD in config:
        acc = {**config}
        acc.pop(CONF_ACCOUNTS, None)
        als.append(acc)
    for cfg in als:
        if not cfg.get(CONF_PASSWORD) and not cfg.get(CONF_TOKEN):
            continue
        acc = Account(hass, cfg)
        coordinator = DevicesCoordinator(acc)
        await acc.async_check_auth()
        await coordinator.async_config_entry_first_refresh()
        hass.data[DOMAIN][CONF_ACCOUNTS][acc.uid] = acc
        hass.data[DOMAIN]["coordinators"][coordinator.name] = coordinator

    for platform in SUPPORTED_DOMAINS:
        hass.async_create_task(async_load_platform(hass, platform, DOMAIN, {}, config))

    return True


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up CatLink from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN].setdefault(CONF_ACCOUNTS, {})
    hass.data[DOMAIN].setdefault(CONF_DEVICES, {})
    hass.data[DOMAIN].setdefault("coordinators", {})
    hass.data[DOMAIN].setdefault("add_entities", {})
    hass.data[DOMAIN]["config"] = {}

    # Create account from config entry
    cfg = {**config_entry.data, **config_entry.options}
    acc = Account(hass, cfg)
    coordinator = DevicesCoordinator(acc)
    
    try:
        await acc.async_check_auth()
        await coordinator.async_config_entry_first_refresh()
    except Exception as exc:
        _LOGGER.error("Failed to set up CatLink account: %s", exc)
        return False

    # Store account and coordinator
    hass.data[DOMAIN][CONF_ACCOUNTS][acc.uid] = acc
    hass.data[DOMAIN]["coordinators"][coordinator.name] = coordinator
    
    # Store config entry reference
    coordinator.config_entry = config_entry

    # Set up all platforms
    await hass.config_entries.async_forward_entry_setups(config_entry, SUPPORTED_DOMAINS)

    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        config_entry, SUPPORTED_DOMAINS
    )
    
    if unload_ok:
        # Clean up stored data
        cfg = {**config_entry.data, **config_entry.options}
        phone = cfg.get("phone")
        phone_iac = cfg.get("phone_iac", "86")
        uid = f"{phone_iac}-{phone}"
        
        hass.data[DOMAIN][CONF_ACCOUNTS].pop(uid, None)
        
        # Clean up coordinators
        coordinators_to_remove = []
        for name, coordinator in hass.data[DOMAIN]["coordinators"].items():
            if coordinator.account.uid == uid:
                coordinators_to_remove.append(name)
        
        for name in coordinators_to_remove:
            hass.data[DOMAIN]["coordinators"].pop(name, None)

    return unload_ok
