import logging
import math

from homeassistant import core
from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.util.percentage import (
    percentage_to_ranged_value,
    ranged_value_to_percentage,
)
from homeassistant.util.scaling import int_states_in_range

from .ApplianceTypes import ApplianceTypes
from .api.XiaoDuAPI import XiaoDuAPI
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# 新风一般 3 档；小度只提供 +/- 步进，具体档数待"开机中"的 detail 数据确认后再调
SPEED_RANGE = (1, 3)


async def async_setup_entry(hass: core.HomeAssistant, config_entry, async_add_entities):
    api = hass.data[DOMAIN][config_entry.entry_id]
    entities = []
    A = ApplianceTypes()
    for device_id in api:
        aapi: XiaoDuAPI = api[device_id]
        # 判断是否是新风(fan)设备
        if not A.is_fan(aapi.applianceTypes):
            continue
        detail = await aapi.get_detail()
        if detail == []:
            continue
        name = detail['appliance']['friendlyName']
        if_onS = str(detail['appliance']['stateSetting']['turnOnState']['value']).lower()
        if_on = if_onS == 'on'
        entities.append(XiaoDuFan(api[device_id], name, if_on, detail['appliance']))
    async_add_entities(entities, update_before_add=True)


class XiaoDuFan(FanEntity):
    """新风：开关 + 风速。小度只有风速 +/- 步进，故用档位差值逐档调节。"""

    def __init__(self, api: XiaoDuAPI, name: str, if_on: bool, detail):
        self._api = api
        self._attr_name = name
        self._group_name = detail.get('groupName')
        self._bot_name = detail.get('botName')
        self._attr_unique_id = f"{api.applianceId}_fan"
        self._attr_supported_features = (FanEntityFeature.SET_SPEED | FanEntityFeature.TURN_ON | FanEntityFeature.TURN_OFF)
        self._attr_speed_count = int_states_in_range(SPEED_RANGE)
        self._attr_is_on = if_on
        # 当前档位 1..speed_count，来自 stateSetting.fanSpeed；未知时为 None
        self._current_gear = None
        self.detail = None

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._api.applianceId)},
            "name": self._attr_name,
            "manufacturer": "小度",
            "model": self._bot_name,
            "suggested_area": self._group_name,
        }

    @property
    def is_on(self):
        return self._attr_is_on

    @property
    def percentage(self):
        if not self._attr_is_on or not self._current_gear:
            return 0
        return ranged_value_to_percentage(SPEED_RANGE, self._current_gear)

    async def async_turn_on(self, percentage=None, preset_mode=None, **kwargs):
        await self._api.switch_on()
        self._attr_is_on = True
        if percentage is not None:
            await self.async_set_percentage(percentage)
        self.async_schedule_update_ha_state(True)

    async def async_turn_off(self, **kwargs):
        await self._api.switch_off()
        self._attr_is_on = False
        self.async_schedule_update_ha_state(True)

    async def async_set_percentage(self, percentage):
        if percentage == 0:
            await self.async_turn_off()
            return
        target_gear = math.ceil(percentage_to_ranged_value(SPEED_RANGE, percentage))
        current = self._current_gear or 1
        if target_gear > current:
            for _ in range(target_gear - current):
                await self._api.fan_speed_up()
        elif target_gear < current:
            for _ in range(current - target_gear):
                await self._api.fan_speed_down()
        self._current_gear = target_gear
        self.async_schedule_update_ha_state(True)

    async def async_update(self):
        self.detail = await self._api.get_detail()
        detail = self.detail['appliance']
        stateSetting = detail['stateSetting']
        turnOnState = str(stateSetting['turnOnState']['value']).lower()
        self._attr_is_on = turnOnState == 'on'
        if 'fanSpeed' in stateSetting:
            try:
                self._current_gear = int(stateSetting['fanSpeed']['value'])
            except (ValueError, TypeError):
                self._current_gear = None
