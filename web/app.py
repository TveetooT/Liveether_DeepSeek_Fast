from aiohttp import web
from aiogram.webhook import aiohttp_server
from bot.dispatcher import setup_dispatcher
from config import Config
from web.stats import stats_handler
from web.admin import admin_login, admin_users, admin_delete, admin_ban, admin_stats, admin_logout
import logging

logger = logging.getLogger(__name__)

async def on_startup(app):
    bot, dp = app['bot'], app['dp']
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_webhook(Config.WEBHOOK_URL, allowed_updates=dp.resolve_used_update_types())
    logger.info(f"Webhook set to {Config.WEBHOOK_URL}")

def create_app():
    bot, dp = setup_dispatcher()
    app = web.Application()
    app['bot'] = bot
    app['dp'] = dp

    # Маршруты
    app.router.add_get("/", lambda r: web.Response(text="OK"))
    app.router.add_get("/health", lambda r: web.Response(text="OK"))
    app.router.add_get("/stats", stats_handler)
    app.router.add_get("/admin", admin_login)
    app.router.add_post("/admin", admin_login)
    app.router.add_get("/admin/users", admin_users)
    app.router.add_post("/admin/delete/{user_id}", admin_delete)
    app.router.add_post("/admin/ban/{user_id}", admin_ban)
    app.router.add_get("/admin/stats", admin_stats)
    app.router.add_get("/admin/logout", admin_logout)

    # Webhook endpoint
    webhook_requests = aiohttp_server.SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_requests.register(app, path="/webhook")

    app.on_startup.append(on_startup)
    return app