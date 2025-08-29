"""The component."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_DEVICES, CONF_PASSWORD, CONF_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.helpers.discovery import async_load_platform
from homeassistant.helpers.entity_component import EntityComponent

from .const import (
    _LOGGER,
    CONF_ACCOUNTS,
    CONF_API_BASE,
    CONF_LANGUAGE,
    CONF_PHONE,
    CONF_PHONE_IAC,
    DOMAIN,
    SCAN_INTERVAL,
    SUPPORTED_DOMAINS,
)
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

    # Check if we have YAML accounts to migrate
    als = config.get(CONF_ACCOUNTS) or []
    if CONF_PASSWORD in config:
        acc = {**config}
        acc.pop(CONF_ACCOUNTS, None)
        als.append(acc)

    # Migrate YAML configurations to config entries
    migrated_accounts = []
    for cfg in als:
        if not cfg.get(CONF_PASSWORD) and not cfg.get(CONF_TOKEN):
            continue
            
        # Create unique ID for this account
        phone = cfg.get(CONF_PHONE) or cfg.get("phone")
        phone_iac = cfg.get(CONF_PHONE_IAC) or cfg.get("phone_iac", "86")
        if not phone:
            _LOGGER.warning("Skipping YAML account with no phone number")
            continue
            
        unique_id = f"{phone_iac}-{phone}"
        
        # Check if config entry already exists
        existing_entry = None
        for entry in hass.config_entries.async_entries(DOMAIN):
            if entry.unique_id == unique_id:
                existing_entry = entry
                break
        
        if existing_entry:
            _LOGGER.info("Config entry already exists for account %s, skipping YAML migration", unique_id)
            migrated_accounts.append(unique_id)
            continue
        
        # Prepare config data for migration
        import_data = {
            CONF_PHONE: phone,
            CONF_PHONE_IAC: phone_iac,
            CONF_PASSWORD: cfg.get(CONF_PASSWORD),
        }
        
        # Add optional fields
        if cfg.get(CONF_API_BASE) or cfg.get("api_base"):
            import_data[CONF_API_BASE] = cfg.get(CONF_API_BASE) or cfg.get("api_base")
        if cfg.get(CONF_LANGUAGE) or cfg.get("language"):
            import_data[CONF_LANGUAGE] = cfg.get(CONF_LANGUAGE) or cfg.get("language")
        if cfg.get("scan_interval"):
            import_data["scan_interval"] = cfg.get("scan_interval")
        if cfg.get("empty_weight"):
            import_data["empty_weight"] = cfg.get("empty_weight")
        if cfg.get("max_samples_litter"):
            import_data["max_samples_litter"] = cfg.get("max_samples_litter")
            
        # Trigger import flow
        _LOGGER.info("Migrating YAML configuration for account %s to config entry", unique_id)
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": "import"},
                data=import_data,
            )
        )
        migrated_accounts.append(unique_id)

    # If all accounts were migrated or already exist as config entries, skip YAML entity creation
    if als and len(migrated_accounts) == len(als):
        _LOGGER.info("All YAML accounts migrated to config entries, skipping YAML entity setup")
        return True

    # For any remaining accounts that couldn't be migrated, continue with YAML setup
    component = EntityComponent(_LOGGER, DOMAIN, hass, SCAN_INTERVAL)
    hass.data[DOMAIN]["component"] = component
    await component.async_setup(config)

    for cfg in als:
        if not cfg.get(CONF_PASSWORD) and not cfg.get(CONF_TOKEN):
            continue
            
        phone = cfg.get(CONF_PHONE) or cfg.get("phone")
        phone_iac = cfg.get(CONF_PHONE_IAC) or cfg.get("phone_iac", "86")
        if not phone:
            continue
            
        unique_id = f"{phone_iac}-{phone}"
        if unique_id in migrated_accounts:
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
