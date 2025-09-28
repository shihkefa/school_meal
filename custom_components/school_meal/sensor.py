from homeassistant.components.sensor import SensorEntity
from homeassistant.util import dt as dt_util
from datetime import timedelta
import aiohttp
from .const import DOMAIN, BASE_URL, MENU_TYPES

DISH_URL = "https://fatraceschool.k12ea.gov.tw/dish"

async def async_setup_entry(hass, entry, async_add_entities):
    school_id = entry.data["school_id"]

    entities = []
    today = dt_util.now().date()
    
    for i in range(8):  # 0=今日, 1=前一天, ... 7=前七天
        target_date = today - timedelta(days=i)
        date_str = target_date.strftime("%Y-%m-%d")
        
        # 相對日期名稱
        if i == 0:
            rel_name = "今日"
        else:
            rel_name = f"前{i}天"
        
        for menu_type in MENU_TYPES:
            name = f"{rel_name}{MENU_TYPES[menu_type]}"
            entities.append(SchoolMealSensor(hass, school_id, menu_type, date_str, name))

    async_add_entities(entities, True)

class SchoolMealSensor(SensorEntity):
    def __init__(self, hass, school_id, menu_type, date_str, display_name):
        self._hass = hass
        self._school_id = school_id
        self._menu_type = menu_type
        self._date_str = date_str
        self._attr_name = display_name  # 使用相對日期名稱
        self._attr_unique_id = f"{school_id}_{menu_type}_{date_str}"
        self._state = None
        self._attr_extra_state_attributes = {}

    async def async_update(self):
        meal_url = (
            f"{BASE_URL}?SchoolId={self._school_id}"
            f"&period={self._date_str}&KitchenId=all&MenuType={self._menu_type}"
        )

        async with aiohttp.ClientSession() as session:
            async with session.get(meal_url) as resp:
                meal_data = await resp.json()

            if meal_data["data"]:
                self._state = "有供餐"
                first = meal_data["data"][0]
                batch_id = first.get("BatchDataId")

                dishes = []
                if batch_id:
                    dish_url = f"https://fatraceschool.k12ea.gov.tw/dish?BatchDataId={batch_id}"
                    async with session.get(dish_url) as resp2:
                        dish_data = await resp2.json()
                    if dish_data.get("data"):
                        dishes = [
                            {
                                "name": d.get("DishName"),
                                "type": d.get("DishType"),
                                "picture": f"https://fatraceschool.k12ea.gov.tw/dish/pic/{d.get('DishId')}"
                            }
                            for d in dish_data["data"]
                        ]

                self._attr_extra_state_attributes = {
                    "meal": first,
                    "dishes": dishes
                }
            else:
                self._state = "無供餐"
                self._attr_extra_state_attributes = {}

    @property
    def state(self):
        return self._state
