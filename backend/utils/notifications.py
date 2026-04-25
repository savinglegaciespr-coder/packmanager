import os
import logging
import httpx

_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

logger = logging.getLogger(__name__)


async def send_telegram_message(text: str) -> None:
    if not _BOT_TOKEN or not _CHAT_ID:
        return
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            await client.post(
                f"https://api.telegram.org/bot{_BOT_TOKEN}/sendMessage",
                json={"chat_id": _CHAT_ID, "text": text},
            )
    except Exception as exc:
        logger.warning("Telegram notification failed: %s", exc)
