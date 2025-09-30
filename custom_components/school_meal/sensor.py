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

    async def async_update_data():
        """抓取供餐與菜單資料"""
        today = dt_util.now().date()
        data = {}

        async with aiohttp.ClientSession() as session:
            for i in range(8):  # 今日+前七天
                target_date = today - timedelta(days=i)
                date_str = target_date.strftime("%Y-%m-%d")

                if i == 0:
                    rel_name = "今日"
                else:
                    rel_name = f"前{i}天"

                for menu_type in MENU_TYPES:
                    name = f"{rel_name}{MENU_TYPES[menu_type]}"
                    meal_url = (
                        f"{BASE_URL}?SchoolId={school_id}"
                        f"&period={date_str}&KitchenId=all&MenuType={menu_type}"
                    )

                    try:
                        async with async_timeout.timeout(10):
                            async with session.get(meal_url) as resp:
                                meal_data = await resp.json()
                    except Exception as e:
                        _LOGGER.error("無法抓取供餐資料: %s", e)
                        continue

                    state = "無供餐"
                    meal = {}
                    dishes = []

                    if meal_data.get("data"):
                        state = "有供餐"
                        meal = meal_data["data"][0]
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

                    data[f"v2_{school_id}_{menu_type}_{date_str}"] = {
                        "name": name,
                        "state": state,
                        "meal": meal,
                        "dishes": dishes,
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
    today = dt_util.now().date()
    for i in range(8):
        target_date = today - timedelta(days=i)
        date_str = target_date.strftime("%Y-%m-%d")

        if i == 0:
            rel_name = "今日"
        else:
            rel_name = f"前{i}天"

        for menu_type in MENU_TYPES:
            name = f"{rel_name}{MENU_TYPES[menu_type]}"
            unique_id = f"v2_{school_id}_{menu_type}_{date_str}"
            entities.append(SchoolMealSensor(coordinator, school_id, unique_id, name))

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
        return "未知"

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data.get(self._attr_unique_id)
        if data:
            return {
                "meal": data["meal"],
                "dishes": data["dishes"],
            }
        return {}

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._school_id)},
            "name": f"學校供餐 ({self._school_id})",
            "manufacturer": "教育部 校園食材登錄平臺",
            "model": "School Meal API",
        }



