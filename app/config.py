import os
from dataclasses import dataclass
from typing import List


def _parse_admin_ids(raw: str | None) -> List[int]:
    if not raw:
        return []
    ids: List[int] = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            ids.append(int(part))
        except ValueError:
            continue
    return ids


@dataclass
class AppConfig:
    telegram_bot_token: str
    telegram_admin_ids: List[int]
    chatwoot_base_url: str
    host: str
    port: int
    locale: str
    rate_limit_per_sec: int


def load_config() -> AppConfig:
    telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    telegram_admin_ids = _parse_admin_ids(os.getenv("TELEGRAM_ADMIN_IDS"))
    chatwoot_base_url = os.getenv("CHATWOOT_BASE_URL", "").rstrip("/")
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    locale = os.getenv("LOCALE", "ru").strip()
    rate_limit_per_sec = int(os.getenv("RATE_LIMIT_PER_SEC", "25"))

    return AppConfig(
        telegram_bot_token=telegram_bot_token,
        telegram_admin_ids=telegram_admin_ids,
        chatwoot_base_url=chatwoot_base_url,
        host=host,
        port=port,
        locale=locale,
        rate_limit_per_sec=rate_limit_per_sec,
    )
