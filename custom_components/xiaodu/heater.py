"""地暖实体。

Home Assistant 没有独立的 `heater` 平台域，地暖本质上是 climate 实体，
所以它由 ``climate.py`` 的 async_setup_entry 负责注册；这里只放实体类本身，
把地暖的逻辑从空调里独立出来，便于维护。
"""
import logging

from homeassistant.components.climate import ClimateEntity, ClimateEntityFeature, HVACMode
from homeassistant.const import UnitOfTemperature, ATTR_TEMPERATURE

from .api.XiaoDuAPI import XiaoDuAPI
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class XiaoDuHeater(ClimateEntity):
    """地暖：只有制热 + 温度调节，用 climate 平台表达（不含模式/风速）。"""

    # 地暖没有绝对温度设定接口，只有 +/- 步进，一次一度
    _DEFAULT_TEMP = 26

    def __init__(self, api: XiaoDuAPI, name: str, if_on: bool, detail):
        self._api = api
        self._attr_name = name
        self._group_name = detail.get('groupName')
        self._bot_name = detail.get('botName')
        self._attr_unique_id = f"{api.applianceId}_heater"
        self._attr_supported_features = (ClimateEntityFeature.TURN_ON | ClimateEntityFeature.TURN_OFF | ClimateEntityFeature.TARGET_TEMPERATURE)
        # 地暖只有制热和关机两种状态
        self._attr_hvac_modes = [HVACMode.HEAT, HVACMode.OFF]
        self._attr_temperature_unit = UnitOfTemperature.CELSIUS
        self._attr_min_temp = 16
        self._attr_max_temp = 32
        self._attr_target_temperature_step = 1
        self._attr_hvac_mode = HVACMode.HEAT if if_on else HVACMode.OFF
        self._attr_target_temperature = self._DEFAULT_TEMP
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

    async def async_turn_on(self):
        await self._api.switch_on()
        self.async_schedule_update_ha_state(True)

    async def async_turn_off(self):
        await self._api.switch_off()
        self.async_schedule_update_ha_state(True)

    async def async_set_hvac_mode(self, hvac_mode):
        if hvac_mode == HVACMode.OFF:
            await self._api.switch_off()
        else:
            await self._api.switch_on()
        self.async_schedule_update_ha_state(True)

    async def async_set_temperature(self, **kwargs):
        """只有 +/- 步进，按当前目标温度与新温度的差值逐度调节（与空调一致）。"""
        temperature = kwargs.get(ATTR_TEMPERATURE, self._DEFAULT_TEMP)
        current = self.target_temperature or self._DEFAULT_TEMP
        if current < temperature:
            for _ in range(int(temperature - current)):
                await self._api.temperature_up()
        else:
            for _ in range(int(current - temperature)):
                await self._api.temperature_down()
        self.async_schedule_update_ha_state(True)

    async def async_update(self):
        self.detail = await self._api.get_detail()
        detail = self.detail['appliance']
        stateSetting = detail['stateSetting']
        if 'temperature' in stateSetting:
            self._attr_target_temperature = stateSetting['temperature']['value']
        turnOnState = str(stateSetting['turnOnState']['value']).lower()
        self._attr_hvac_mode = HVACMode.HEAT if turnOnState == 'on' else HVACMode.OFF
