import asyncio
import json
import logging
import os
from contextlib import suppress
from typing import Any, Dict, List, Optional

from aiohttp import web
from aiogram import Bot
from aiogram.enums import ParseMode
from aiolimiter import AsyncLimiter
from dotenv import load_dotenv

from app.config import load_config, AppConfig
from app.locales import Locales


def create_support_link_direct(base_url: str, account_id: int, conversation_id: int) -> str:
    return f"{base_url}/app/accounts/{account_id}/conversations/{conversation_id}"


def _get_str(d: Dict[str, Any], key: str) -> Optional[str]:
    value = d.get(key)
    return value if isinstance(value, str) else None


def _get_int(d: Dict[str, Any], key: str) -> Optional[int]:
    value = d.get(key)
    return value if isinstance(value, int) else None


async def chatwoot_webhook_handler(request: web.Request) -> web.Response:
    app = request.app
    cfg: AppConfig = app["config"]
    bot: Bot = app["bot"]
    limiter: AsyncLimiter = app["limiter"]
    locales: Locales = app["locales"]

    raw = await request.read()

    with suppress(json.JSONDecodeError):
        body = json.loads(raw.decode("utf-8"))
    if not isinstance(body, dict):
        return web.Response(status=400, text="invalid payload")

    logging.warning("Webhook Chatwoot received!")

    event_message = _get_str(body, "event")
    if event_message != "message_created":
        return web.Response(text="ok", status=200)

    # Extract sender and assignee safely
    conversation = body.get("conversation", {}) if isinstance(body.get("conversation"), dict) else {}
    meta = conversation.get("meta", {}) if isinstance(conversation.get("meta"), dict) else {}

    sender = body.get("sender") if isinstance(body.get("sender"), dict) else meta.get("sender", {})
    sender = sender if isinstance(sender, dict) else {}

    assignee = meta.get("assignee", {}) if isinstance(meta.get("assignee"), dict) else {}

    if bool(sender.get("blocked", False)):
        return web.Response(status=200)

    name_user = _get_str(sender, "name")
    if not name_user:
        return web.Response(status=200)

    assignee_name = _get_str(assignee, "name") or ""

    if name_user == assignee_name:
        return web.Response(status=200)

    # Detect conversation/account ids
    account_id = (
        _get_int(conversation, "account_id")
        or _get_int(assignee, "account_id")
        or _get_int(assignee, "id")
        or _get_int(body.get("account", {}) if isinstance(body.get("account"), dict) else {}, "id")
    )

    conversation_id = (
        _get_int(conversation, "id")
        or (_get_int(conversation.get("messages", [{}])[0] if isinstance(conversation.get("messages"), list) and conversation.get("messages") else {}, "conversation_id"))
    )

    if not (isinstance(account_id, int) and isinstance(conversation_id, int)):
        return web.Response(status=200)

    direct_link = create_support_link_direct(
        base_url=cfg.chatwoot_base_url,
        account_id=account_id,
        conversation_id=conversation_id,
    )

    message_text = locales.t(
        cfg.locale,
        "notifications.support_new_message",
        user_name=name_user,
        assignee_name=assignee_name,
        link=direct_link,
    )

    # Send to admins with rate limiting
    tasks: List[asyncio.Task] = []
    for admin_id in cfg.telegram_admin_ids:
        async def send_once(chat_id: int, text: str) -> None:
            async with limiter:
                await bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True,
                )
        tasks.append(asyncio.create_task(send_once(admin_id, message_text)))

    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)

    return web.Response(text="success", status=200)


async def health_handler(_: web.Request) -> web.Response:
    return web.Response(text="ok", status=200)


async def create_app() -> web.Application:
    load_dotenv()
    cfg = load_config()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

    app = web.Application()
    app["config"] = cfg
    app["locales"] = Locales(base_dir=os.path.join(os.path.dirname(__file__), "..", "locales"), default_locale=cfg.locale)

    async def on_startup(app: web.Application) -> None:
        app["bot"] = Bot(token=cfg.telegram_bot_token)
        app["limiter"] = AsyncLimiter(max_rate=cfg.rate_limit_per_sec, time_period=1)

    async def on_cleanup(app: web.Application) -> None:
        bot: Bot = app["bot"]
        await bot.session.close()

    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)

    app.router.add_get("/health", health_handler)
    app.router.add_post("/webhooks/chatwoot", chatwoot_webhook_handler)
    return app


if __name__ == "__main__":
    load_dotenv()
    cfg = load_config()

    web.run_app(asyncio.run(create_app()), host=cfg.host, port=cfg.port)
