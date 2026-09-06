import random
import time
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from bot.services.database import DatabaseService
from bot.services.validator import Validator
from bot.models.user import User

class ProfileService:
    def __init__(self, db: DatabaseService):
        self.db = db

    async def get_profile(self, user_id: int) -> Optional[User]:
        return await self.db.get_user(user_id)

    async def update_field(self, user_id: int, field: str, value):
        await self.db.update_field(user_id, field, value)

    async def set_action(self, user_id: int, action: str):
        await self.db.update_field(user_id, "action", action)

    async def get_action(self, user_id: int) -> Optional[str]:
        return await self.db.get_field(user_id, "action")

    async def start_form(self, user_id: int):
        # Проверяем, приняты ли правила
        form_filled = await self.db.get_field(user_id, "form")
        if form_filled != "true":
            await self.set_action(user_id, "rules")
        else:
            await self.set_action(user_id, "name")

    async def save_form_data(self, user_id: int, action: str, text: str) -> bool:
        ok, error, value = Validator.validate_field(action, text)
        if not ok:
            return False, error
        if action == "age":
            await self.db.update_field(user_id, action, value)
        else:
            await self.db.update_field(user_id, action, value)
        return True, None

    async def get_next_action(self, current_action: str) -> Optional[str]:
        NEXT_ACTION = {
            "name": "age",
            "age": "univer",
            "univer": "about",
            "about": "requirements",
            "requirements": "region",
            "region": "city",
            "city": "confirm",
        }
        return NEXT_ACTION.get(current_action)

    async def get_unseen_profile(self, user_id: int, city: str) -> Optional[Dict]:
        candidates = await self.db.get_unseen_users(user_id, city)
        if not candidates:
            return None
        now = time.time()
        weights = []
        for u in candidates:
            last_active = u.get("last_active")
            if last_active:
                try:
                    if isinstance(last_active, str):
                        dt = datetime.fromisoformat(last_active.replace('Z', '+00:00'))
                        last_ts = dt.timestamp()
                    else:
                        last_ts = last_active.timestamp()
                except Exception:
                    last_ts = 0
            else:
                last_ts = 0
            views = u.get("views_count") or 0
            days_since_active = (now - last_ts) / 86400
            weight = (days_since_active + 1) / (views + 1)
            weights.append(weight)
        selected = random.choices(candidates, weights=weights, k=1)[0]
        # Записать просмотр
        await self.db.add_view(user_id, selected["user_id"])
        await self.db.increment_views_count(selected["user_id"])
        await self.db.update_field(user_id, "last_active", datetime.now(timezone.utc).isoformat())
        return selected