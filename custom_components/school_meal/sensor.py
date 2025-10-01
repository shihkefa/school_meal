from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)
from homeassistant.util import dt as dt_util
from datetime import timedelta
import aiohttp
import async_timeout
import logging

from .const import DOMAIN, BASE_URL, MENU_TYPES

_LOGGER = logging.getLogger(__name__)
DISH_URL = "https://fatraceschool.k12ea.gov.tw/dish"

async def async_setup_entry(hass, entry, async_add_entities):
    school_id = entry.data["school_id"]
    selected_menu_types = entry.data.get("menu_types", list(MENU_TYPES.keys()))

    async def async_update_data():
        today = dt_util.now().date()
        data = {}

        async with aiohttp.ClientSession() as session:
            for i in range(8):  # 今日 + 前七天
                target_date = today - timedelta(days=i)
                date_str = target_date.strftime("%Y-%m-%d")
                rel_name = "今日" if i == 0 else f"前{i}天"

                for menu_type in selected_menu_types:
                    state = "無供餐"
                    meal = {}
                    dishes = []

                    meal_url = f"{BASE_URL}?SchoolId={school_id}&period={date_str}&KitchenId=all&MenuType={menu_type}"
                    try:
                        async with async_timeout.timeout(10):
                            async with session.get(meal_url) as resp:
                                meal_data = await resp.json()
                    except Exception as e:
                        _LOGGER.error("無法抓取供餐資料: %s", e)
                        meal_data = {}

                    if meal_data.get("data"):
                        meal = meal_data["data"][0]
                        state = "有供餐"
                        batch_id = meal.get("BatchDataId")

                        if batch_id:
                            dish_url = f"{DISH_URL}?BatchDataId={batch_id}"
                            try:
                                async with async_timeout.timeout(10):
                                    async with session.get(dish_url) as resp2:
                                        dish_data = await resp2.json()
                                if dish_data.get("data"):
                                    dishes = [
                                        {
                                            "name": d.get("DishName"),
                                            "type": d.get("DishType"),
                                            "picture": f"https://fatraceschool.k12ea.gov.tw/dish/pic/{d.get('DishId')}",
                                        }
                                        for d in dish_data["data"]
                                    ]
                            except Exception as e:
                                _LOGGER.warning("無法抓取菜單資料: %s", e)

                    unique_id = f"v2_{school_id}_{menu_type}_{i}"
                    data[unique_id] = {
                        "name": f"{rel_name}{MENU_TYPES[menu_type]}",
                        "state": state,
                        "meal": meal,
                        "dishes": dishes,
                        "date": date_str,
                    }

        return data

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="school_meal",
        update_method=async_update_data,
        update_interval=timedelta(minutes=15),
    )

    await coordinator.async_config_entry_first_refresh()

    entities = []
    for i in range(8):
        for menu_type in selected_menu_types:
            unique_id = f"v2_{school_id}_{menu_type}_{i}"
            rel_name = "今日" if i == 0 else f"前{i}天"
            entities.append(SchoolMealSensor(coordinator, school_id, unique_id, f"{rel_name}{MENU_TYPES[menu_type]}"))

    async_add_entities(entities, True)


class SchoolMealSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, school_id, unique_id, display_name):
        super().__init__(coordinator)
        self._attr_name = display_name
        self._attr_unique_id = unique_id
        self._school_id = school_id

    @property
    def state(self):
        data = self.coordinator.data.get(self._attr_unique_id)
        if data:
            return data["state"]
        return "無供餐"

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data.get(self._attr_unique_id)
        if data:
            return {
                "meal": data["meal"],
                "dishes": data["dishes"],
                "date": data.get("date"),
            }
        return {"meal": {}, "dishes": [], "date": None}

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._school_id)},
            "name": f"學校供餐 ({self._school_id})",
            "manufacturer": "教育部 校園食材登錄平臺",
            "model": "School Meal API",
        }
