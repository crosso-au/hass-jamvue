"""Shared helpers for the JamVue integration."""
from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.webhook import async_generate_path
from homeassistant.core import HomeAssistant
from homeassistant.helpers.network import NoURLAvailableError, get_url


@dataclass(frozen=True)
class WebhookUrl:
    """A single webhook URL option to present to the user.

    Either ``url`` is set (resolved), or ``hint`` is set (couldn't resolve, so
    we show guidance on how to make this address available).
    """

    label: str
    url: str | None = None
    hint: str | None = None


# (label, get_url kwargs, hint shown when it can't be resolved).
#
# "External" respects your configured external URL (e.g. homeassistant.example.com)
# or a Nabu Casa cloud URL if that's what's set up. "Internal" is the
# local-network address.
_URL_VARIANTS: tuple[tuple[str, dict, str], ...] = (
    (
        "External (use this for cloud services)",
        {"allow_internal": False, "prefer_external": True},
        "Not configured — set an External URL under Settings → System → "
        "Network, enable Home Assistant Cloud (Nabu Casa), or set an override in "
        "Configure. This is required if JamVue runs in the cloud.",
    ),
    (
        "Internal (same local network)",
        {"allow_external": False},
        "Not configured — set an Internal URL under Settings → System → Network.",
    ),
)


def normalize_base_url(base: str | None) -> str | None:
    """Clean a user-supplied base URL, or return None if blank.

    Trims whitespace and trailing slashes, and assumes https:// if no scheme
    was given (e.g. "homeassistant.example.com" -> "https://homeassistant.example.com").
    """
    if not base:
        return None
    base = base.strip().rstrip("/")
    if not base:
        return None
    if "://" not in base:
        base = f"https://{base}"
    return base


def webhook_urls(
    hass: HomeAssistant, webhook_id: str, override_base: str | None = None
) -> list[WebhookUrl]:
    """Return the webhook URL options to show the user.

    The External and Internal slots are always present: when one can't be
    resolved, its ``url`` is None and ``hint`` explains how to fix it. An
    optional override, if set, is shown first and suppresses the "not
    configured" hints (the user has already told us which address to use).
    """
    path = async_generate_path(webhook_id)
    results: list[WebhookUrl] = []
    seen: set[str] = set()

    override = normalize_base_url(override_base)
    if override:
        url = f"{override}{path}"
        seen.add(url)
        results.append(WebhookUrl("Custom (your configured override)", url=url))

    show_hints = override is None
    for label, kwargs, hint in _URL_VARIANTS:
        try:
            base = get_url(hass, **kwargs)
        except NoURLAvailableError:
            if show_hints:
                results.append(WebhookUrl(label, hint=hint))
            continue
        url = f"{base}{path}"
        if url in seen:
            continue
        seen.add(url)
        results.append(WebhookUrl(label, url=url))

    return results


def webhook_urls_markdown(
    hass: HomeAssistant, webhook_id: str, override_base: str | None = None
) -> str:
    """Render the webhook URL options as a markdown block for the UI."""
    items = webhook_urls(hass, webhook_id, override_base)
    lines: list[str] = []
    for item in items:
        if item.url:
            lines.append(f"**{item.label}:**\n`{item.url}`")
        else:
            lines.append(f"**{item.label}:**\n_{item.hint}_")

    if not lines:
        path = async_generate_path(webhook_id)
        return f"`https://<your-home-assistant>{path}`"
    return "\n\n".join(lines)
