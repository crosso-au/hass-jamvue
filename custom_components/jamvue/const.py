"""Constants for the JamVue integration."""

DOMAIN = "jamvue"

CONF_WEBHOOK_ID = "webhook_id"
# Optional user-supplied base URL to use when displaying the webhook address,
# overriding Home Assistant's auto-detected internal/external URLs.
CONF_BASE_URL = "base_url"

# Event fired on the HA bus whenever a webhook payload arrives.
# Users can listen for this in automations.
EVENT_TRACK_RESOLVED = f"{DOMAIN}_track_resolved"

# Payload fields accepted from the JamVue webhook.
ATTR_TRACK_ID = "track_id"
ATTR_TITLE = "title"
ATTR_ARTIST = "artist"
ATTR_ALBUM = "album"
ATTR_ALBUM_ART_URL = "album_art_url"
ATTR_DURATION = "duration"
# Seconds into the track at the moment JamVue resolved it. Drives the live
# progress bar; Home Assistant advances it automatically while playing.
ATTR_POSITION = "position"
ATTR_STATE = "state"
ATTR_PLAYING = "playing"

# Values for the optional `state` field telling the player to stop/pause.
STATE_HINTS_IDLE = {"idle", "stopped", "stop", "off", "ended"}
STATE_HINTS_PAUSED = {"paused", "pause"}
