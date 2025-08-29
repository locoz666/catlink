"""The component."""

from homeassistant.const import CONF_DEVICES
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .account import Account
from .device import Device
from ..binary_sensor import CatlinkBinarySensorEntity
from ..button import CatlinkButtonEntity
from ..const import _LOGGER, DOMAIN, SUPPORTED_DOMAINS
from ..modules.feeder_device import FeederDevice
from ..modules.fresh2_feeder_device import Fresh2FeederDevice
from ..modules.litterbox import LitterBox
from ..modules.pure2_device import Pure2Device
from ..modules.scooper_device import ScooperDevice
from ..number import CatlinkNumberEntity
from ..select import CatlinkSelectEntity
from ..sensor import CatlinkSensorEntity
from ..switch import CatlinkSwitchEntity
from ..models.additional_cfg import AdditionalDeviceConfig


class DevicesCoordinator(DataUpdateCoordinator):
    """Devices Coordinator for CatLink integration."""

    def __init__(self, account: "Account") -> None:
        """Initialize the devices coordinator."""
        super().__init__(
            account.hass,
            _LOGGER,
            name=f"{DOMAIN}-{account.uid}-{CONF_DEVICES}",
            update_interval=account.update_interval,
        )
        self.account = account
        self._subs = {}
        self.config_entry = None  # Will be set by __init__.py
        
        # Get device-specific configuration from YAML config
        yaml_config = self.hass.data[DOMAIN]["config"].get(CONF_DEVICES, {})
        self.additional_config = [
            AdditionalDeviceConfig(**cfg) for cfg in yaml_config
        ]

    async def _async_update_data(self) -> dict:
        """Update data via API."""
        dls = await self.account.get_devices()
        for dat in dls:
            # Get device-specific config from YAML or config entry
            additional_config = next(
                (cfg for cfg in self.additional_config if cfg.mac == dat.get("mac")),
                None,
            )
            
            # If not found and has config entry, create default config from config entry
            if not additional_config and self.config_entry:
                cfg_data = {**self.config_entry.data, **self.config_entry.options}
                additional_config = AdditionalDeviceConfig(
                    mac=dat.get("mac", ""),
                    empty_weight=cfg_data.get("empty_weight", 0.0),
                    max_samples_litter=cfg_data.get("max_samples_litter", 24),
                )
            did = dat.get("id")
            if not did:
                continue
            old = self.hass.data[DOMAIN][CONF_DEVICES].get(did)
            if old:
                dvc = old
                dvc.update_data(dat)
            else:
                typ = dat.get("deviceType")
                match typ:
                    case "SCOOPER":
                        dvc = ScooperDevice(dat, self, additional_config)
                    case "LITTER_BOX_599":  # SCOOPER C1
                        dvc = LitterBox(dat, self, additional_config)
                    case "FEEDER":
                        dvc = FeederDevice(dat, self, additional_config)
                    case "FEEDER_PRO":  # Fresh2 feeder series (fresh2-standard, fresh2-pro)
                        dvc = Fresh2FeederDevice(dat, self, additional_config)
                    case "PUREPRO":  # Pure2 water fountain series (Pure2, Pure2 Pro, Pure2 UV)
                        dvc = Pure2Device(dat, self, additional_config)
                    case _:
                        dvc = Device(dat, self)
                self.hass.data[DOMAIN][CONF_DEVICES][did] = dvc
                _LOGGER.debug(
                    "Created device '%s' (Type: %s, ID: %s, MAC: %s) with config: %s", 
                    dvc.name, 
                    dvc.type, 
                    dvc.id, 
                    dvc.mac,
                    additional_config
                )
            await dvc.async_init()
            for d in SUPPORTED_DOMAINS:
                await self.update_hass_entities(d, dvc)
        return self.hass.data[DOMAIN][CONF_DEVICES]

    async def update_hass_entities(self, domain, dvc) -> None:
        """Update Home Assistant entities."""
        hdk = f"hass_{domain}"
        add = self.hass.data[DOMAIN]["add_entities"].get(domain)
        if not add or not hasattr(dvc, hdk):
            return
        for k, cfg in getattr(dvc, hdk).items():
            key = f"{domain}.{k}.{dvc.id}"
            new = None
            if key in self._subs:
                pass
            elif domain == "sensor":
                new = CatlinkSensorEntity(k, dvc, cfg)
            elif domain == "binary_sensor":
                new = CatlinkBinarySensorEntity(k, dvc, cfg)
            elif domain == "switch":
                new = CatlinkSwitchEntity(k, dvc, cfg)
            elif domain == "select":
                new = CatlinkSelectEntity(k, dvc, cfg)
            elif domain == "button":
                new = CatlinkButtonEntity(k, dvc, cfg)
            elif domain == "number":
                new = CatlinkNumberEntity(k, dvc, cfg)
            if new:
                self._subs[key] = new
                add([new])
