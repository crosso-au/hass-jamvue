"""JamVue Home Assistant integration.

Receives webhook POSTs from JamVue when a vinyl track is identified,
and exposes a media_player entity reflecting what is currently playing.
"""
from __future__ import annotations

import logging

from aiohttp.web import Request, Response, json_response

from homeassistant.components.webhook import async_register, async_unregister
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import CONF_BASE_URL, CONF_WEBHOOK_ID, DOMAIN, EVENT_TRACK_RESOLVED
from .helpers import webhook_urls

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["media_player"]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the JamVue integration."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up JamVue from a config entry."""
    webhook_id = entry.data[CONF_WEBHOOK_ID]

    async def handle_webhook(
        hass: HomeAssistant, webhook_id: str, request: Request
    ) -> Response:
        """Handle an incoming JamVue webhook POST."""
        try:
            data = await request.json()
        except ValueError:
            _LOGGER.warning("JamVue webhook received a non-JSON payload")
            return json_response({"status": "error", "reason": "invalid_json"}, status=400)

        if not isinstance(data, dict):
            _LOGGER.warning(
                "JamVue webhook expected a JSON object, got %s", type(data).__name__
            )
            return json_response(
                {"status": "error", "reason": "expected_object"}, status=400
            )

        _LOGGER.debug("JamVue webhook payload: %s", data)
        hass.bus.async_fire(EVENT_TRACK_RESOLVED, data)
        return json_response({"status": "ok"})

    async_register(
        hass,
        DOMAIN,
        "JamVue Track Resolved",
        webhook_id,
        handle_webhook,
        local_only=False,
    )

    resolved = [
        item
        for item in webhook_urls(hass, webhook_id, entry.options.get(CONF_BASE_URL))
        if item.url
    ]
    if resolved:
        for item in resolved:
            _LOGGER.info("JamVue webhook ready — %s: %s", item.label, item.url)
    else:
        _LOGGER.warning(
            "JamVue webhook registered (id: %s) but no reachable URL is "
            "configured — set an internal/external URL in Settings → System → "
            "Network so you have an address to give JamVue.",
            webhook_id,
        )

    hass.data[DOMAIN][entry.entry_id] = {CONF_WEBHOOK_ID: webhook_id}

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a JamVue config entry.

    Tear down only after the platform unloads cleanly, so a failed unload
    leaves the (still-working) webhook in place rather than a half-removed state.
    """
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        async_unregister(hass, entry.data[CONF_WEBHOOK_ID])
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
