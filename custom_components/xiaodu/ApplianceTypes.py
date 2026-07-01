class ApplianceTypes:
    def __init__(self):
        pass

    def LIGHT(self):
        return ['LIGHT']

    def SWITCH(self):
        return ['SOCKET', 'WASHING_MACHINE', 'SWITCH', 'WINDOW_OPENER', 'CLOTHES_RACK']

    def COVER(self):
        return ['CURTAIN']

    def CLIMATE(self):
        return ['AIR_CONDITION']

    def HEATER(self):
        # 地暖：走 climate 平台（只制热 + 温度），不再当普通开关
        return ['HEATER']

    def FAN(self):
        # 新风：走 fan 平台（开关 + 风速），不再当普通开关
        return ['AIR_FRESHER']

    def BUTTON(self):
        return ['CLOTHES_RACK']

    def LOCK(self):
        return ['DOOR_LOCK']

    def is_switch(self, applianceTypes):
        A = ApplianceTypes()
        switch = A.SWITCH()
        for i in applianceTypes:
            if i in switch:
                return True
        return False

    def is_light(self, applianceTypes):
        A = ApplianceTypes()
        switch = A.LIGHT()
        for i in applianceTypes:
            if i in switch:
                return True
        return False

    def is_cover(self, applianceTypes):
        A = ApplianceTypes()
        switch = A.COVER()
        for i in applianceTypes:
            if i in switch:
                return True
        return False

    def is_climate(self, applianceTypes):
        A = ApplianceTypes()
        switch = A.CLIMATE()
        for i in applianceTypes:
            if i in switch:
                return True
        return False

    def is_heater(self, applianceTypes):
        A = ApplianceTypes()
        heater = A.HEATER()
        for i in applianceTypes:
            if i in heater:
                return True
        return False

    def is_fan(self, applianceTypes):
        A = ApplianceTypes()
        fan = A.FAN()
        for i in applianceTypes:
            if i in fan:
                return True
        return False

    def is_button(self, applianceTypes):
        A = ApplianceTypes()
        switch = A.BUTTON()
        for i in applianceTypes:
            if i in switch:
                return True
        return False

    def is_lock(self, applianceTypes):
        A = ApplianceTypes()
        switch = A.LOCK()
        for i in applianceTypes:
            if i in switch:
                return True
        return False
