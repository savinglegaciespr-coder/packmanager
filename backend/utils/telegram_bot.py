import logging
import os

import httpx

from utils.notifications import send_telegram_message

_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
_BACKEND_URL = os.environ.get("BACKEND_URL", "").rstrip("/")
_RAILWAY_TOKEN = os.environ.get("RAILWAY_TOKEN", "")
_RAILWAY_SERVICE_ID = "b69effe0-0ad1-4623-be92-4943417f9681"
_RAILWAY_ENV_ID = "cea78451-6128-43cb-b7e7-fe319c3ba63c"

logger = logging.getLogger(__name__)

_HELP = (
    "Comandos disponibles:\n"
    "/status — verifica si el backend está activo\n"
    "/health — ejecuta health check\n"
    "/restart — dispara redeploy en Railway\n"
    "/help — muestra este mensaje"
)


async def _railway_redeploy() -> str:
    if not _RAILWAY_TOKEN:
        return (
            "⚠️ RAILWAY_TOKEN no configurado.\n"
            "Redeploy manual: Railway dashboard → packmanager → Redeploy"
        )
    query = (
        "mutation { serviceInstanceDeploy("
        f'serviceId: "{_RAILWAY_SERVICE_ID}", '
        f'environmentId: "{_RAILWAY_ENV_ID}", '
        "latestCommit: true) }"
    )
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(
                "https://backboard.railway.app/graphql/v2",
                headers={
                    "Authorization": f"Bearer {_RAILWAY_TOKEN}",
                    "Content-Type": "application/json",
                },
                json={"query": query},
            )
        data = r.json()
        if data.get("data", {}).get("serviceInstanceDeploy"):
            return "🔄 Redeploy disparado en Railway."
        return f"⚠️ Railway respondió: {data}"
    except Exception as exc:
        logger.warning("Railway redeploy failed: %s", exc)
        return f"❌ No se pudo contactar Railway: {exc}"


async def handle_update(data: dict) -> None:
    message = data.get("message") or data.get("channel_post") or {}
    if not message:
        return

    chat_id = str(message.get("chat", {}).get("id", ""))
    if not _CHAT_ID or chat_id != _CHAT_ID:
        return

    command = (message.get("text") or "").strip().split()[0].split("@")[0]

    if command == "/status":
        await send_telegram_message("✅ Backend activo y en ejecución.")
    elif command == "/health":
        base = _BACKEND_URL or "http://localhost:8000"
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                r = await client.get(f"{base}/health")
            if r.status_code == 200:
                await send_telegram_message("✅ Health check OK")
            else:
                await send_telegram_message(f"⚠️ Health check: status {r.status_code}")
        except Exception as exc:
            await send_telegram_message(f"❌ Health check falló: {exc}")
    elif command == "/restart":
        reply = await _railway_redeploy()
        await send_telegram_message(reply)
    elif command == "/help":
        await send_telegram_message(_HELP)


async def register_webhook() -> None:
    if not _BOT_TOKEN or not _BACKEND_URL:
        return
    webhook_url = f"{_BACKEND_URL}/telegram/webhook/{_BOT_TOKEN}"
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            await client.post(
                f"https://api.telegram.org/bot{_BOT_TOKEN}/setWebhook",
                json={"url": webhook_url},
            )
    except Exception as exc:
        logger.warning("Telegram webhook registration failed: %s", exc)
