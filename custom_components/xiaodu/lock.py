import logging

from homeassistant import core
from homeassistant.components.lock import LockEntity

from . import ApplianceTypes
from .api.XiaoDuAPI import XiaoDuAPI
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: core.HomeAssistant, config_entry, async_add_entities):
    api = hass.data[DOMAIN][config_entry.entry_id]
    entities = []
    A = ApplianceTypes()
    for device_id in api:
        aapi: XiaoDuAPI = api[device_id]
        # 判断是否是lock设备
        applianceTypes = aapi.applianceTypes
        if not A.is_lock(applianceTypes):
            continue
        detail = await aapi.get_detail()
        if detail == []:
            continue
        name = detail['appliance']['friendlyName']
        try:
            if 'turnOnState' not in detail['appliance']['attributes']:
                if_onS = str(detail['appliance']['attributes']['lockState']['value']).lower()
                if_onS = "on" if if_onS == "unlocked" else "off"
            else:
                if_onS = str(detail['appliance']['attributes']['turnOnState']['value']).lower()
        except Exception as e:
            _LOGGER.error(e)
            continue
        if if_onS == "on":
            if_on = True
        else:
            if_on = False
        entities.append(XiaoDuLock(api[device_id], name, if_on, detail['appliance']))
    async_add_entities(entities, update_before_add=True)


class XiaoDuLock(LockEntity):

    def __init__(self, api: XiaoDuAPI, name: str, if_on: bool, detail):
        self._api = api
        self._attr_unique_id = f"{api.applianceId}_lock"
        self._attr_is_open = if_on
        self._attr_is_locked = not if_on
        self._attr_name = name
        self._group_name = detail.get('groupName')
        self._bot_name = detail.get('botName')
        self.pColorMode = None
        self.effectList = {}
        if if_on:
            self._attr_icon = "mdi:lock-open-outline"
        else:
            self._attr_icon = "mdi:lock"

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._api.applianceId)},
            "name": self._attr_name,
            "manufacturer": "小度",
            "model": self._bot_name,
            "suggested_area": self._group_name,
        }

    async def async_update(self):
        # self._is_on = await self._api.switch_status()
        detail = await self._api.get_detail()
        detail = detail['appliance']
        try:
            if 'turnOnState' not in detail['attributes']:
                if_onS = str(detail['attributes']['lockState']['value']).lower()
                if_onS = "on" if if_onS == "unlocked" else "off"
            else:
                if_onS = str(detail['attributes']['turnOnState']['value']).lower()
        except Exception as e:
            print(f"请求小度出错: {e}")
            return
        if if_onS == "on":
            if_on = True
        else:
            if_on = False
        self._attr_is_open = if_on
        self._attr_is_locked = not if_on
