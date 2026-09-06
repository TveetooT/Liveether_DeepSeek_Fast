from bot.services.database import DatabaseService

class ViewService:
    def __init__(self, db: DatabaseService):
        self.db = db

    async def handle_like(self, liker_id: int, liked_id: int):
        # Проверяем, есть ли взаимный лайк
        mutual_state = await self.db.get_field(
            liked_id, "state", table="views",
            additional_field="viewed_user_id", additional_value=liker_id
        )
        if mutual_state == "like_unseen":
            # Взаимный лайк → уведомления
            liker_username = await self.db.get_field(liker_id, "username")
            liked_username = await self.db.get_field(liked_id, "username")
            liker_name = f"@{liker_username}" if liker_username else "пользователь без username"
            liked_name = f"@{liked_username}" if liked_username else "пользователь без username"
            # Отправка сообщений будет выполняться через бота, но здесь мы только обновляем состояние
            # Возвращаем имена для отправки
            await self.db.update_view_state(liked_id, liker_id, "seen")
            await self.db.update_view_state(liker_id, liked_id, "seen")
            return True, liker_name, liked_name
        else:
            await self.db.update_view_state(liker_id, liked_id, "like_unseen")
            return False, None, None

    async def handle_dislike(self, user_id: int, viewed_id: int):
        await self.db.update_view_state(user_id, viewed_id, "seen")

    async def handle_report(self, reporter_id: int, reported_id: int):
        current = await self.db.get_field(reported_id, "reports") or 0
        await self.db.update_field(reported_id, "reports", current + 1)
        await self.db.update_view_state(reporter_id, reported_id, "seen")