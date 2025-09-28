import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN

class SchoolMealConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            return self.async_create_entry(
                title=f"SchoolId {user_input['school_id']}",
                data=user_input,
            )

        data_schema = vol.Schema({
            vol.Required("school_id"): str
        })

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )
