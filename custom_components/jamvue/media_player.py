"""JamVue media player entity."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
    MediaType,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import (
    ATTR_ALBUM,
    ATTR_ALBUM_ART_URL,
    ATTR_ARTIST,
    ATTR_DURATION,
    ATTR_PLAYING,
    ATTR_POSITION,
    ATTR_STATE,
    ATTR_TITLE,
    ATTR_TRACK_ID,
    DOMAIN,
    EVENT_TRACK_RESOLVED,
    STATE_HINTS_IDLE,
    STATE_HINTS_PAUSED,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the JamVue media player from a config entry."""
    async_add_entities([JamVueMediaPlayer(entry)])


class JamVueMediaPlayer(MediaPlayerEntity):
    """Represents the currently-playing record on JamVue."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_icon = "mdi:music"
    _attr_supported_features = MediaPlayerEntityFeature(0)
    _attr_media_content_type = MediaType.MUSIC
    _attr_should_poll = False

    def __init__(self, entry: ConfigEntry) -> None:
        """Initialize the entity."""
        self._attr_unique_id = f"{entry.entry_id}_player"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "JamVue",
            "manufacturer": "JamVue",
            "model": "Know what's playing",
        }
        self._attr_state = MediaPlayerState.IDLE
        self._track_id: str | None = None
        self._title: str | None = None
        self._artist: str | None = None
        self._album: str | None = None
        self._album_art_url: str | None = None
        self._duration: int | None = None
        self._position: int | None = None
        self._position_updated_at: datetime | None = None

    @property
    def media_title(self) -> str | None:
        return self._title

    @property
    def media_artist(self) -> str | None:
        return self._artist

    @property
    def media_album_name(self) -> str | None:
        return self._album

    @property
    def media_image_url(self) -> str | None:
        return self._album_art_url

    @property
    def media_duration(self) -> int | None:
        return self._duration

    @property
    def media_position(self) -> int | None:
        return self._position

    @property
    def media_position_updated_at(self) -> datetime | None:
        """When the position was last set; HA extrapolates from here."""
        return self._position_updated_at

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        attrs: dict[str, Any] = {}
        if self._track_id:
            attrs[ATTR_TRACK_ID] = self._track_id
        return attrs

    async def async_added_to_hass(self) -> None:
        """Subscribe to track-resolved events when added."""
        self.async_on_remove(
            self.hass.bus.async_listen(EVENT_TRACK_RESOLVED, self._handle_track)
        )

    @callback
    def _handle_track(self, event: Event) -> None:
        """Update state from a webhook payload."""
        data = event.data

        # Optional explicit stop/pause signalling from JamVue.
        state_hint = str(data.get(ATTR_STATE, "")).lower()
        playing_flag = data.get(ATTR_PLAYING)

        if state_hint in STATE_HINTS_IDLE or playing_flag is False:
            self._reset_media()
            self._attr_state = MediaPlayerState.IDLE
            self.async_write_ha_state()
            return

        if state_hint in STATE_HINTS_PAUSED:
            self._freeze_position()
            self._attr_state = MediaPlayerState.PAUSED
            self.async_write_ha_state()
            return

        self._track_id = data.get(ATTR_TRACK_ID)
        self._title = data.get(ATTR_TITLE)
        self._artist = data.get(ATTR_ARTIST)
        self._album = data.get(ATTR_ALBUM)
        self._album_art_url = data.get(ATTR_ALBUM_ART_URL)
        self._duration = self._coerce_seconds(data.get(ATTR_DURATION))

        # Position is optional. When JamVue tells us how far into the track it
        # is, HA shows an accurate, self-advancing progress bar. Without it we
        # leave position unset rather than guess (vinyl is often resolved
        # mid-track, so 0 would be misleading).
        position = self._coerce_seconds(data.get(ATTR_POSITION))
        if position is not None:
            self._position = position
            self._position_updated_at = dt_util.utcnow()
        else:
            self._position = None
            self._position_updated_at = None

        if self._title or self._artist:
            self._attr_state = MediaPlayerState.PLAYING
        else:
            self._attr_state = MediaPlayerState.IDLE

        self.async_write_ha_state()

    def _reset_media(self) -> None:
        """Clear current track metadata."""
        self._track_id = None
        self._title = None
        self._artist = None
        self._album = None
        self._album_art_url = None
        self._duration = None
        self._position = None
        self._position_updated_at = None

    def _freeze_position(self) -> None:
        """Capture the current position when pausing so the bar stops correctly."""
        if self._position is None or self._position_updated_at is None:
            return
        elapsed = (dt_util.utcnow() - self._position_updated_at).total_seconds()
        self._position = max(0, int(self._position + elapsed))
        self._position_updated_at = dt_util.utcnow()

    @staticmethod
    def _coerce_seconds(value: Any) -> int | None:
        """Coerce a seconds value to int; HA requires ints for duration/position."""
        if value is None:
            return None
        try:
            return int(float(value))
        except (TypeError, ValueError):
            _LOGGER.debug("JamVue ignoring non-numeric seconds value: %r", value)
            return None
