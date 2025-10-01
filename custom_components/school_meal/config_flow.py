import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN, MENU_TYPES

class SchoolMealConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 2

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            # 將使用者輸入中文拆成 key
            raw_input = user_input.get("menu_types", "")
            selected_keys = []
            for name in raw_input.split(","):
                name = name.strip()
                for k, v in MENU_TYPES.items():
                    if v == name:
                        selected_keys.append(k)
                        break

            # 如果沒有匹配到合法餐別，給預設值
            if not selected_keys:
                selected_keys = list(MENU_TYPES.keys())

            user_input["menu_types"] = selected_keys
            return self.async_create_entry(
                title=f"SchoolId {user_input['school_id']}",
                data=user_input,
            )

        data_schema = vol.Schema({
            vol.Required(
                "school_id",
                description={"suggested_value": "請輸入學校ID"}
            ): str,
            vol.Required(
                "menu_types",
                default="早點,午餐,午點",
                description={"suggested_value": "輸入餐別並以,分隔。例:午餐 or 早點,午餐,午點"}
            ): str
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema
        )
