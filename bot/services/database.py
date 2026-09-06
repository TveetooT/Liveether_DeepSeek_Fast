import asyncio
from typing import Optional, List, Dict, Any
from supabase import create_client, Client
from config import Config
from bot.models.user import User

class DatabaseService:
    def __init__(self):
        self.client: Client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)

    async def _run_sync(self, func, *args, **kwargs):
        return await asyncio.to_thread(func, *args, **kwargs)

    # ---- Пользователи ----
    async def upsert_user(self, user_data: Dict[str, Any]) -> None:
        def _upsert():
            self.client.table("users").upsert(user_data, on_conflict="user_id").execute()
        await self._run_sync(_upsert)

    async def get_user(self, user_id: int) -> Optional[User]:
        def _get():
            resp = self.client.table("users").select("*").eq("user_id", user_id).execute()
            if resp.data:
                return User(**resp.data[0])
            return None
        return await self._run_sync(_get)

    async def update_field(self, user_id: int, field: str, value, table: str = "users",
                           additional_field: str = None, additional_value = None) -> None:
        def _update():
            q = self.client.table(table).update({field: value}).eq("user_id", user_id)
            if additional_field and additional_value is not None:
                q = q.eq(additional_field, additional_value)
            q.execute()
        await self._run_sync(_update)

    async def get_field(self, user_id: int, field: str, table: str = "users",
                        additional_field: str = None, additional_value = None) -> Any:
        def _get():
            q = self.client.table(table).select(field).eq("user_id", user_id)
            if additional_field and additional_value is not None:
                q = q.eq(additional_field, additional_value)
            resp = q.execute()
            if resp.data:
                return resp.data[0].get(field)
            return None
        return await self._run_sync(_get)

    async def delete_user(self, user_id: int) -> None:
        def _delete():
            self.client.table("views").delete().eq("user_id", user_id).execute()
            self.client.table("views").delete().eq("viewed_user_id", user_id).execute()
            self.client.table("users").delete().eq("user_id", user_id).execute()
        await self._run_sync(_delete)

    # ---- Просмотры ----
    async def add_view(self, user_id: int, viewed_user_id: int, state: str = "unseen") -> None:
        def _add():
            self.client.table("views").upsert(
                {"user_id": user_id, "viewed_user_id": viewed_user_id, "state": state},
                on_conflict="user_id,viewed_user_id",
                ignore_duplicates=True
            ).execute()
        await self._run_sync(_add)

    async def increment_views_count(self, user_id: int) -> None:
        def _inc():
            resp = self.client.table("users").select("views_count").eq("user_id", user_id).execute()
            if resp.data:
                current = resp.data[0].get("views_count") or 0
                self.client.table("users").update({"views_count": current + 1}).eq("user_id", user_id).execute()
        await self._run_sync(_inc)

    async def get_likes_for_user(self, user_id: int) -> List[Dict]:
        def _get():
            resp = self.client.table("views").select("*").eq("viewed_user_id", user_id).eq("state", "like_unseen").execute()
            return resp.data
        return await self._run_sync(_get)

    async def update_view_state(self, user_id: int, viewed_user_id: int, state: str) -> None:
        await self.update_field(user_id, "state", state, table="views",
                                additional_field="viewed_user_id", additional_value=viewed_user_id)

    # ---- Профили и поиск ----
    async def get_unseen_users(self, user_id: int, city: str) -> List[Dict]:
        def _call():
            resp = self.client.rpc("get_unseen_users", {"p_user_id": user_id, "p_city": city}).execute()
            return resp.data
        return await self._run_sync(_call)

    # ---- Администрирование ----
    async def clear_all_data(self) -> None:
        def _clear():
            self.client.table("views").delete().neq("user_id", -1).execute()
            self.client.table("users").delete().neq("user_id", -1).execute()
        await self._run_sync(_clear)

    async def recreate_database(self) -> None:
        def _recreate():
            self.client.rpc("recreate_database").execute()
        await self._run_sync(_recreate)

    async def get_all_users(self, offset: int, limit: int) -> List[Dict]:
        def _get():
            resp = self.client.table("users").select("*").order("user_id").range(offset, offset + limit - 1).execute()
            return resp.data
        return await self._run_sync(_get)

    async def get_stats(self, since: Optional[str] = None) -> Dict:
        """Получить статистику за период (since - ISO строка даты/времени)"""
        def _stats():
            users_query = self.client.table("users").select("user_id", count="exact")
            forms_query = self.client.table("users").select("user_id", count="exact").eq("form", "true")
            views_query = self.client.table("views").select("user_id", count="exact")
            likes_query = self.client.table("views").select("user_id", count="exact").eq("state", "like_unseen")
            cities_query = self.client.table("users").select("city").eq("form", "true")

            if since:
                users_query = users_query.gte("created_at", since)
                forms_query = forms_query.gte("created_at", since)
                views_query = views_query.gte("created_at", since)
                likes_query = likes_query.gte("created_at", since)
                cities_query = cities_query.gte("created_at", since)

            total_users = users_query.execute().count
            filled_forms = forms_query.execute().count
            total_views = views_query.execute().count
            total_likes = likes_query.execute().count
            city_data = cities_query.execute().data
            from collections import Counter
            city_counter = Counter(row["city"] for row in city_data if row.get("city"))
            top_cities = city_counter.most_common(5)

            return {
                "total_users": total_users,
                "filled_forms": filled_forms,
                "total_views": total_views,
                "total_likes": total_likes,
                "top_cities": top_cities,
            }
        return await self._run_sync(_stats)

    # ---- Бан ----
    async def toggle_ban(self, user_id: int) -> bool:
        def _get():
            resp = self.client.table("users").select("banned").eq("user_id", user_id).execute()
            return resp.data[0]["banned"] if resp.data else False
        current = await self._run_sync(_get)
        new_val = not current
        await self.update_field(user_id, "banned", str(new_val).lower())
        return new_val