from aiohttp import web
from bot.services.database import DatabaseService
from bot.services.keyboard import KeyboardFactory
import hashlib
import asyncio
import html
from config import Config

COOKIE_NAME = "admin_session"
COOKIE_MAX_AGE = 86400 * 7

def set_admin_cookie(response, value):
    response.set_cookie(COOKIE_NAME, value, max_age=COOKIE_MAX_AGE, httponly=True, secure=True, path='/')

def is_admin(request):
    cookie_val = request.cookies.get(COOKIE_NAME)
    if cookie_val:
        expected = hashlib.sha256((Config.ROOT_CODE + "_salt").encode()).hexdigest()
        return cookie_val == expected
    return False

async def admin_login(request):
    if request.method == "POST":
        data = await request.post()
        code = data.get("code")
        if code == Config.ROOT_CODE:
            resp = web.HTTPFound("/admin/users")
            set_admin_cookie(resp, hashlib.sha256((Config.ROOT_CODE + "_salt").encode()).hexdigest())
            return resp
        return web.Response(text="Неверный код", status=403)

    html_content = """
    <!DOCTYPE html>
    <html><head><meta charset="utf-8"><title>Вход в админку</title>
    <style>body{font-family:sans-serif;max-width:400px;margin:40px auto;padding:20px;background:#f0f2f5;}
    input,button{display:block;width:100%;padding:12px;margin:10px 0;border-radius:8px;border:1px solid #ccc;font-size:16px;}
    button{background:#0f3460;color:white;border:none;cursor:pointer;}</style>
    </head><body>
    <h2>Вход в панель управления</h2>
    <form method="POST">
        <input type="password" name="code" placeholder="Введите ROOT_CODE" required>
        <button type="submit">Войти</button>
    </form>
    </body></html>
    """
    return web.Response(text=html_content, content_type='text/html')

async def admin_users(request):
    if not is_admin(request):
        return web.HTTPFound("/admin")
    page = int(request.query.get('page', 1))
    per_page = 20
    offset = (page - 1) * per_page

    db = DatabaseService()
    users = await db.get_all_users(offset, per_page)

    rows = ""
    for u in users:
        rows += f"""
        <tr>
            <td>{u['user_id']}</td>
            <td>@{u.get('username', '-')}</td>
            <td>{html.escape(u.get('name') or '')}</td>
            <td>{u.get('age', '')}</td>
            <td>{html.escape(u.get('city') or '')}</td>
            <td>{u.get('form') == 'true' and '✅' or '❌'}</td>
            <td>{u.get('reports', 0)}</td>
            <td>{u.get('views_count', 0)}</td>
            <td>{u.get('banned') and '🚫' or ''}</td>
            <td>
                <form style="display:inline" method="POST" action="/admin/delete/{u['user_id']}" onsubmit="return confirm('Удалить анкету?')">
                    <button type="submit">🗑️</button>
                </form>
                <form style="display:inline" method="POST" action="/admin/ban/{u['user_id']}">
                    <button type="submit">{"🚫" if not u.get('banned') else "✅"}</button>
                </form>
            </td>
        </tr>
        """

    html_content = f"""
    <!DOCTYPE html>
    <html><head><meta charset="utf-8"><title>Пользователи</title>
    <style>
        body{{font-family:sans-serif;max-width:1200px;margin:20px auto;padding:20px;background:#f0f2f5;}}
        table{{width:100%;border-collapse:collapse;background:white;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.1);}}
        th,td{{padding:10px;text-align:left;border-bottom:1px solid #eee;}}
        th{{background:#0f3460;color:white;}}
        .nav{{display:flex;gap:10px;margin-top:20px;}}
        .nav a{{background:#0f3460;color:white;padding:8px 16px;border-radius:8px;text-decoration:none;}}
        .logout{{float:right;}}
    </style>
    </head><body>
        <h1>👥 Пользователи <span class="logout"><a href="/admin/logout">Выйти</a></span></h1>
        <table>
            <tr><th>ID</th><th>Username</th><th>Имя</th><th>Возраст</th><th>Город</th><th>Анкета</th><th>Жалобы</th><th>Просмотры</th><th>Бан</th><th>Действия</th></tr>
            {rows}
        </table>
        <div class="nav">
            <a href="?page={page-1 if page>1 else 1}">◀ Назад</a>
            <a href="?page={page+1}">Вперёд ▶</a>
        </div>
        <p><a href="/admin/stats">📊 Расширенная статистика</a></p>
    </body></html>
    """
    return web.Response(text=html_content, content_type='text/html')

async def admin_delete(request):
    if not is_admin(request):
        return web.HTTPFound("/admin")
    user_id = int(request.match_info['user_id'])
    db = DatabaseService()
    await db.delete_user(user_id)
    return web.HTTPFound("/admin/users")

async def admin_ban(request):
    if not is_admin(request):
        return web.HTTPFound("/admin")
    user_id = int(request.match_info['user_id'])
    db = DatabaseService()
    await db.toggle_ban(user_id)
    return web.HTTPFound("/admin/users")

async def admin_stats(request):
    if not is_admin(request):
        return web.HTTPFound("/admin")
    db = DatabaseService()
    # Расширенная статистика (можно реализовать отдельный метод)
    def _stats():
        total_users = db.client.table("users").select("user_id", count="exact").execute().count
        banned_users = db.client.table("users").select("user_id", count="exact").eq("banned", "true").execute().count
        reports_gt5 = db.client.table("users").select("user_id", count="exact").gt("reports", 5).execute().count
        views_total = db.client.table("views").select("user_id", count="exact").execute().count
        likes_total = db.client.table("views").select("user_id", count="exact").eq("state", "like_unseen").execute().count
        return {
            "total": total_users,
            "banned": banned_users,
            "reports_gt5": reports_gt5,
            "views": views_total,
            "likes": likes_total,
        }
    data = await asyncio.to_thread(_stats)

    html_content = f"""
    <!DOCTYPE html>
    <html><head><meta charset="utf-8"><title>Админ-статистика</title>
    <style>body{{font-family:sans-serif;max-width:600px;margin:40px auto;padding:20px;background:#f0f2f5;}}
    .card{{background:white;padding:15px;margin:10px 0;border-radius:12px;box-shadow:0 2px 8px rgba(0,0,0,0.1);display:flex;justify-content:space-between;}}
    .value{{font-size:24px;font-weight:bold;color:#0f3460;}}
    </style>
    </head><body>
        <h1>📊 Расширенная статистика</h1>
        <div class="card"><span>👥 Всего пользователей</span><span class="value">{data['total']}</span></div>
        <div class="card"><span>🚫 Забаненных</span><span class="value">{data['banned']}</span></div>
        <div class="card"><span>⚠️ Жалоб >5</span><span class="value">{data['reports_gt5']}</span></div>
        <div class="card"><span>👁️ Всего просмотров</span><span class="value">{data['views']}</span></div>
        <div class="card"><span>❤️ Лайков</span><span class="value">{data['likes']}</span></div>
        <p><a href="/admin/users">← Назад к пользователям</a></p>
    </body></html>
    """
    return web.Response(text=html_content, content_type='text/html')

async def admin_logout(request):
    resp = web.HTTPFound("/admin")
    resp.del_cookie(COOKIE_NAME)
    return resp