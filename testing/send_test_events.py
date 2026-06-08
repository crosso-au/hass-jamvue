#!/usr/bin/env python3
"""Send example JamVue webhook events to a Home Assistant instance.

This lets you exercise the integration end-to-end without a real turntable:
it POSTs a sequence of payloads covering every state the integration handles
(playing, paused, stopped) so you can watch `media_player.jamvue` react.

Usage:
    python send_test_events.py <webhook_url>
    python send_test_events.py <webhook_url> --delay 5
    python send_test_events.py <webhook_url> --only paused
    python send_test_events.py --list

The webhook URL is shown during integration setup, e.g.:
    https://homeassistant.example.com/api/webhook/<id>
    http://192.168.1.111:8123/api/webhook/<id>

You can also set it via the JAMVUE_WEBHOOK_URL environment variable instead of
passing it on the command line.

Only the Python standard library is used — no `pip install` required.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

# Each scenario is (name, payload). They run top-to-bottom to simulate a side
# of a record: a couple of tracks, a pause, then the record ending.
SCENARIOS: list[tuple[str, dict]] = [
    (
        "playing_full",
        {
            "title": "Blue in Green",
            "artist": "Miles Davis",
            "album": "Kind of Blue",
            "album_art_url": "https://cdn-p.smehost.net/sites/c5d2b1a28fd246bfafed3b8dbafc1352/wp-content/uploads/1959/04/10-KINDOFBLUE.jpg",
            "track_id": "test-001",
            "duration": 337,
            "position": 42,
        },
    ),
    (
        "playing_minimal",
        {
            "title": "So What",
            "album_art_url": "https://cdn-p.smehost.net/sites/c5d2b1a28fd246bfafed3b8dbafc1352/wp-content/uploads/1959/04/10-KINDOFBLUE.jpg",
            "artist": "Miles Davis",
        },
    ),
    (
        "paused",
        {"state": "paused"},
    ),
    (
        "playing_again",
        {
            "title": "Take Five",
            "artist": "The Dave Brubeck Quartet",
            "album": "Time Out",
            "album_art_url": "https://cdn-p.smehost.net/sites/c5d2b1a28fd246bfafed3b8dbafc1352/wp-content/uploads/1959/04/10-KINDOFBLUE.jpg",
            "track_id": "test-002",
            "duration": 324,
            "position": 90,
        },
    ),
    (
        "stopped_state",
        {"state": "stopped"},
    ),
    (
        "stopped_playing_false",
        {"playing": False},
    ),
]


def send(url: str, name: str, payload: dict, timeout: float = 10.0) -> bool:
    """POST one payload and print the result. Returns False if unreachable."""
    body = json.dumps(payload).encode()
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            text = response.read().decode().strip()
            print(f"  [OK  {response.status}] {name:<22} {json.dumps(payload)}")
            if text:
                print(f"            response: {text}")
        return True
    except urllib.error.HTTPError as err:
        text = err.read().decode().strip()
        print(f"  [ERR {err.code}] {name:<22} server rejected it: {text}")
        return True
    except urllib.error.URLError as err:
        print(f"  [FAIL]      {name:<22} could not reach {url}\n            -> {err.reason}")
        return False


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Send example JamVue webhook events to Home Assistant.",
    )
    parser.add_argument(
        "url",
        nargs="?",
        default=os.environ.get("JAMVUE_WEBHOOK_URL"),
        help="Webhook URL (or set the JAMVUE_WEBHOOK_URL environment variable).",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=3.0,
        help="Seconds to wait between events so you can watch the entity change (default: 3).",
    )
    parser.add_argument(
        "--only",
        metavar="NAME",
        help="Send a single named scenario instead of the whole sequence.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List the available scenarios and exit.",
    )
    args = parser.parse_args()

    if args.list:
        print("Available scenarios:\n")
        for name, payload in SCENARIOS:
            print(f"  {name:<22} {json.dumps(payload)}")
        return 0

    if not args.url:
        parser.error(
            "No webhook URL provided. Pass it as an argument or set "
            "JAMVUE_WEBHOOK_URL. Run with --list to see the test scenarios."
        )

    scenarios = SCENARIOS
    if args.only:
        scenarios = [(n, p) for n, p in SCENARIOS if n == args.only]
        if not scenarios:
            names = ", ".join(n for n, _ in SCENARIOS)
            parser.error(f"Unknown scenario '{args.only}'. Choose from: {names}")

    print(f"Sending {len(scenarios)} event(s) to {args.url}\n")
    for index, (name, payload) in enumerate(scenarios):
        if not send(args.url, name, payload):
            return 1
        if index < len(scenarios) - 1:
            time.sleep(args.delay)

    print("\nDone. Open Home Assistant and check media_player.jamvue.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
