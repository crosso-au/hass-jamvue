"""Config flow for JamVue."""
from __future__ import annotations

import voluptuous as vol

from homeassistant.components.webhook import async_generate_id
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback

from .const import CONF_BASE_URL, CONF_WEBHOOK_ID, DOMAIN
from .helpers import webhook_urls_markdown


class JamVueConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for JamVue."""

    VERSION = 1

    def __init__(self) -> None:
        self._webhook_id: str | None = None

    async def async_step_user(
        self, user_input: dict | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        # Generate the webhook id once and keep it stable across form redisplays.
        if self._webhook_id is None:
            self._webhook_id = async_generate_id()

        if user_input is not None:
            return self.async_create_entry(
                title="JamVue",
                data={CONF_WEBHOOK_ID: self._webhook_id},
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({}),
            description_placeholders={
                "webhook_urls": webhook_urls_markdown(self.hass, self._webhook_id)
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Return the options flow that re-displays the webhook URL."""
        return JamVueOptionsFlow()


class JamVueOptionsFlow(OptionsFlow):
    """Lets the user look up their webhook URL and set an optional URL override."""

    async def async_step_init(
        self, user_input: dict | None = None
    ) -> ConfigFlowResult:
        """Show the webhook URL(s) and let the user override the base URL."""
        if user_input is not None:
            base_url = user_input.get(CONF_BASE_URL, "").strip()
            return self.async_create_entry(title="", data={CONF_BASE_URL: base_url})

        webhook_id = self.config_entry.data[CONF_WEBHOOK_ID]
        current = self.config_entry.options.get(CONF_BASE_URL, "")
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {vol.Optional(CONF_BASE_URL, default=current): str}
            ),
            description_placeholders={
                "webhook_urls": webhook_urls_markdown(
                    self.hass, webhook_id, current or None
                )
            },
        )
