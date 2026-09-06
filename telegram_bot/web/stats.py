from aiohttp import web
from datetime import datetime, timedelta
from bot.services.database import DatabaseService
import asyncio
import logging

logger = logging.getLogger(__name__)

async def stats_handler(request):
    period = request.query.get('period', 'all')
    now = datetime.now()
    since = None
    if period == 'day':
        since = now - timedelta(days=1)
    elif period == 'week':
        since = now - timedelta(days=7)
    elif period == 'month':
        since = now - timedelta(days=30)

    db = DatabaseService()
    try:
        stats_data = await db.get_stats(since.isoformat() if since else None)
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        return web.Response(text="Ошибка получения данных", status=500)

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>📊 Статистика Livether</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 700px; margin: 30px auto; padding: 20px; background: #f0f2f5; color: #1a1a2e; }}
            h1 {{ text-align: center; font-size: 28px; color: #16213e; }}
            .period-buttons {{ display: flex; gap: 10px; justify-content: center; margin-bottom: 20px; }}
            .period-buttons a {{ background: #e0e0e0; padding: 8px 16px; border-radius: 20px; text-decoration: none; color: #333; font-weight: 500; }}
            .period-buttons a.active {{ background: #0f3460; color: white; }}
            .card {{ background: white; padding: 15px 25px; margin: 15px 0; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); display: flex; justify-content: space-between; align-items: center; }}
            .card .label {{ font-weight: 500; color: #555; }}
            .card .value {{ font-size: 26px; font-weight: bold; color: #0f3460; }}
            .city-list {{ list-style: none; padding: 0; margin: 5px 0; }}
            .city-list li {{ display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid #eee; }}
            .badge {{ background: #e94560; color: white; padding: 4px 10px; border-radius: 20px; font-size: 14px; }}
            .footer {{ text-align: center; color: #888; font-size: 14px; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <h1>📊 Статистика Livether</h1>
        <div class="period-buttons">
            <a href="?period=all" class="{'active' if period=='all' else ''}">Всё время</a>
            <a href="?period=day" class="{'active' if period=='day' else ''}">День</a>
            <a href="?period=week" class="{'active' if period=='week' else ''}">Неделя</a>
            <a href="?period=month" class="{'active' if period=='month' else ''}">Месяц</a>
        </div>
        <div class="card"><span class="label">👥 Всего пользователей</span><span class="value">{stats_data['total_users']}</span></div>
        <div class="card"><span class="label">✅ Заполненных анкет</span><span class="value">{stats_data['filled_forms']}</span></div>
        <div class="card"><span class="label">👁️ Всего просмотров</span><span class="value">{stats_data['total_views']}</span></div>
        <div class="card"><span class="label">❤️ Лайков</span><span class="value">{stats_data['total_likes']}</span></div>
        <div class="card" style="flex-direction:column; align-items:stretch;">
            <span class="label" style="margin-bottom:10px;">🏙️ Топ-5 городов</span>
            <ul class="city-list">
                {"".join(f"<li><span>{city}</span><span class='badge'>{count}</span></li>" for city, count in stats_data['top_cities'])}
            </ul>
        </div>
        <div class="footer"><p>🔄 Обновлено: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p></div>
    </body>
    </html>
    """
    return web.Response(text=html_content, content_type='text/html')