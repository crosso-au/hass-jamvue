# Jamvue for Home Assistant

<p align="center"><img src="https://github.com/crosso-au/hass-Jamvue/raw/main/branding/icon.png" alt="Jamvue" width="320"></p>

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![hacs_badge](https://img.shields.io/github/release-date-pre/crosso-au/hass-Jamvue)](https://github.com/crosso-au/hass-Jamvue)
[![hacs_badge](https://badgen.net/github/release/crosso-au/hass-Jamvue)](https://github.com/crosso-au/hass-Jamvue/releases)
[![hacs_badge](https://badgen.net/github/last-commit/crosso-au/hass-Jamvue/main)](https://github.com/crosso-au/hass-Jamvue)

A Home Assistant integration for [Jamvue](https://Jamvue.com) - Jamvue taps your turntable's output directly, no microphone, completely privately - and identifies what's spinning in real time on a dedicated display.

[![hacs_badge](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=crosso-au&repository=hass-Jamvue&category=integration)

## How it works

1. Tap the signal
An RCA Y-splitter sits between your turntable and amplifier. Your music plays normally - Jamvue just listens alongside it.
2. Capture & fingerprint
A USB audio interface feeds the signal to the onboard processor, which creates an acoustic fingerprint in seconds.
3. Match in the cloud
A short audio snippet is sent to our service and matched against a database of tens of millions of tracks. The snippet is never stored - it is discarded immediately after identification.
4. Display the track
Title, artist and your listening history appear on the crisp, dedicated Jamvue display wherever you like.

### Now for Jamvue for HomeAssistant
1. Jamvue fires a webhook `POST` to Home Assistant with the resolved track metadata.
2. This integration receives that webhook and updates a `media_player` entity with the current artist, title, album, and artwork.

It also fires a `Jamvue_track_resolved` event on the Home Assistant event bus for every payload received, so you can build your own automations on top of it.

## Installation

### HACS (recommended)

1. Open HACS → Integrations → ⋮ → **Custom repositories**.
2. Add this repository's URL with category **Integration**.
3. Search for **Jamvue** and install.
4. Restart Home Assistant.

### Manual

Copy the `custom_components/Jamvue` folder into your HA `config/custom_components/` directory and restart.

## Setup

1. Go to **Settings → Devices & Services → Add Integration** and search for **Jamvue**.
2. The setup dialog shows your unique **webhook URL(s)**. Depending on your Home
   Assistant network config, you'll see:
   - **External** - your configured external/Nabu Casa address
     (e.g. `https://homeassistant.example.com/api/webhook/<id>`). Use this if Jamvue
     runs in the cloud.
   - **Internal** - your local-network address
     (e.g. `http://192.168.X.XXX:8123/api/webhook/<id>`). Use this only if Jamvue
     is on the same LAN.
3. Copy the appropriate URL, submit the dialog, and paste it into Jamvue's webhook configuration.

> **Note:** Jamvue must be able to reach this URL. If Jamvue runs in the cloud, your Home Assistant needs to be reachable from the internet (e.g. via [Home Assistant Cloud / Nabu Casa](https://www.nabucasa.com/) or a reverse proxy). The webhook id acts as a secret - **keep the URL private.**

### Finding the URL again

Forgot the URL? You can retrieve it any time without changing it:

- **Settings → Devices & Services → Jamvue → Configure** re-displays the URL(s).
- It's also written to the log at every startup - search **Settings → System → Logs** for `Jamvue webhook`.

### Which external URL is shown?

The **External** URL comes from Home Assistant's own configuration. It prefers the
external address you set under **Settings → System → Network** (e.g.
`https://homeassistant.example.com`), and falls back to your Nabu Casa cloud URL if no
external URL is configured. So if you want your own domain shown, set it there
once and it benefits all of Home Assistant.

If you'd rather not change your global external URL - or you want a different
address *just* for this webhook - open **Jamvue → Configure** and set the
**External URL override**. When set, it's shown first; clear it to go back to the
auto-detected URLs. (This only changes the address displayed/logged; the webhook
itself works on whatever address actually reaches your Home Assistant.)

## Webhook payload

Jamvue will `POST` a JSON **object** to the webhook URL. Supported fields:

| Field | Type | Description |
|-------|------|-------------|
| `title` | string | Track title |
| `artist` | string | Artist name |
| `album_art_url` | string | URL to album artwork |
| `album` | string | **Optional.** Album name |
| `track_id` | string | **Optional.** Jamvue internal track ID |
| `duration` | number | **Optional.** Track duration in seconds |
| `position` | number | **Optional.** Seconds into the track at resolution time. Enables a live, self-advancing progress bar. Omit it (vinyl is often recognised mid-track) and no progress bar is shown |
| `state` | string | **Optional.** `playing` (default), or `idle`/`stopped`/`paused` to change player state |
| `playing` | boolean | **Optional.** `false` is treated the same as `state: "stopped"` |

When a payload includes a `title` or `artist`, the player switches to **Playing**. To signal the record has stopped. Optionally, send `{"state": "stopped"}` (or `{"playing": false}`), which returns the player to **Idle** and clears the metadata.

### Example: track resolved

```json
{
  "title": "Going Down",
  "artist": "Freddie King",
  "album": "Getting Ready...(World)",
  "album_art_url": "https://upload.wikimedia.org/wikipedia/en/thumb/0/08/Getting_Ready...jpg/250px-Getting_Ready...jpg",
  "track_id": "c9dgfj39gfysakgufd83jgfjgf843",
  "duration": 337,
  "position": 42
}
```

### Example: record stopped

```json
{ "state": "stopped" }
```

## Entity

The integration creates a single `media_player.Jamvue` entity. When a track is resolved it enters the `playing` state with full media metadata - artist, title, album, and artwork - ready to display on dashboards or use in automations.

## Automations (examples)

Every webhook payload is re-emitted as a `Jamvue_track_resolved` event, so you can trigger automations directly:

### New Record
Now-playing notification with album art

Pushes phone notifications including the cover image whenever a new track is identified. Quietly skips itself if no artwork came through.

```yaml
automation:
  - alias: "Now playing with artwork"
    trigger:
      - platform: event
        event_type: Jamvue_track_resolved
    condition:
      - condition: template
        value_template: "{{ trigger.event.data.title is defined }}"
    action:
      - service: notify.mobile_app_S26_phone
        data:
          title: "Now spinning"
          message: >
            {{ trigger.event.data.artist }} – {{ trigger.event.data.title }}
            {%- if trigger.event.data.album %} ({{ trigger.event.data.album }}){%- endif %}
          data:
            image: "{{ trigger.event.data.album_art_url | default('') }}"
```

### Special effect for favourite artists
Artist-specific WLED effect

A nod to your favourite artist... pick the artists you want a distinct lighting treatment for and fire a dedicated WLED effect. Easy to extend with more choose branches per artist or genre.

```yaml
automation:
  - alias: "Special effect for favourite artists"
    trigger:
      - platform: event
        event_type: Jamvue_track_resolved
    action:
      - choose:
          - conditions:
              - condition: template
                value_template: >
                  {{ trigger.event.data.artist | lower in
                     ['the rolling stones', 'pink floyd', 'acdc', 'david bowie', 'the who'] }}
            sequence:
              - service: light.turn_on
                target:
                  entity_id: light.wled_living_room
                data:
                  effect: "Aurora"
                  brightness_pct: 40
```

### Jamvue Captain Now
Hand the room over to vinyl

When a record is detected, pause whatever's streaming elsewhere (Music Assistant, Sonos, etc.) so the turntable takes over without two sources fighting. The state == playing check avoids triggering on stop events.

```yaml
automation:
  - alias: "Vinyl takes priority"
    trigger:
      - platform: event
        event_type: Jamvue_track_resolved
    condition:
      - condition: template
        value_template: "{{ trigger.event.data.state | default('playing') != 'stopped' }}"
    action:
      - service: media_player.media_pause
        target:
          entity_id:
            - media_player.music_assistant_living_room
            - media_player.kitchen_speaker
```

### Vinyl mode
Vinyl listening mode (lights down on drop)

When a record starts, dim the Hue strips and kick WLED into a slow ambient preset - your moody, cinematic listening scene. A companion automation restores things when the record stops.

```yaml
automation:
  - alias: "Vinyl mode - on"
    trigger:
      - platform: event
        event_type: Jamvue_track_resolved
    condition:
      - condition: template
        value_template: "{{ trigger.event.data.state | default('playing') != 'stopped' }}"
    action:
      - service: scene.create
        data:
          scene_id: pre_vinyl_lights
          snapshot_entities:
            - light.living_room_hue
            - light.wled_living_room
      - service: light.turn_on
        target:
          entity_id: light.living_room_hue
        data:
          brightness_pct: 25
          rgb_color: [255, 140, 40]
      - service: select.select_option
        target:
          entity_id: select.wled_living_room_preset
        data:
          option: "Slow Ambient"

  - alias: "Vinyl mode - off"
    trigger:
      - platform: event
        event_type: Jamvue_track_resolved
    condition:
      - condition: template
        value_template: "{{ trigger.event.data.state | default('playing') == 'stopped' }}"
    action:
      - service: scene.turn_on
        target:
          entity_id: scene.pre_vinyl_lights
```

## Testing

A small harness in [`testing/`](testing/) fires example webhook events at your
instance so you can confirm everything works before adding your webhook URL to the Jamvue settings.

```bash
python send_test_events.py "https://homeassistant.example.com/api/webhook/<id>"
```

Options:

```bash
python send_test_events.py <url> --delay 5      # wait 5s between events
python send_test_events.py <url> --only paused  # send just one scenario
python send_test_events.py --list               # show all scenarios
```

## Uninstalling

Jamvue for Home Assistant cleans up after itself - there are no stray files, helpers, or background tasks to chase down.

1. **Remove the integration:** Go to **Settings → Devices & Services → Jamvue → ⋮ → Delete**.
   This unregisters the webhook (the URL stops working immediately) and removes the `media_player.Jamvue` entity and the Jamvue device from Home Assistant.
2. **Remove the component (optional):** In HACS, open Jamvue → ⋮ → **Remove**, or delete the `custom_components/Jamvue/` folder manually. Restart Home Assistant.

All integration state lives inside the config entry, which Home Assistant deletes for you in step 1 - so step 2 is just housekeeping.

## License

[MIT](LICENSE)
