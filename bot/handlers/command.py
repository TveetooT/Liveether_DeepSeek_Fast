import html
from aiogram.types import Message
from bot.handlers.base import BaseHandler
from bot.services.profile import ProfileService
from bot.services.view import ViewService
from bot.services.database import DatabaseService
from bot.services.keyboard import KeyboardFactory
from bot.constants import PHRASES, COMMAND_MENU
import asyncio

class CommandHandler(BaseHandler):
    def __init__(self, db: DatabaseService, profile: ProfileService, view: ViewService, bot):
        super().__init__(db, profile, view)
        self.bot = bot

    async def handle(self, message: Message):
        text = message.text
        user_id = message.from_user.id
        username = message.from_user.username

        if text == "/start":
            await self.db.upsert_user({"user_id": user_id})
            if username:
                await self.db.update_field(user_id, "username", username)
            await self.profile.set_action(user_id, "None")
            await self.db.add_view(user_id, user_id, state="seen")
            await message.answer(PHRASES["StartMessage"], parse_mode="HTML")
        elif text == "/form":
            await self.profile.start_form(user_id)
            action = await self.profile.get_action(user_id)
            if action == "rules":
                await message.answer(
                    PHRASES["RulesMessage"],
                    reply_markup=KeyboardFactory.rules_inline(),   # inline-кнопка
                    parse_mode="HTML"
                )
            else:
                await message.answer(PHRASES["nameMessage"], parse_mode="HTML")
        elif text == "/profile":
            await self._show_profile(message, user_id)
        elif text == "/menu":
            await message.answer(PHRASES["Menu"], reply_markup=KeyboardFactory.main_menu(), parse_mode="HTML")
            await self.profile.set_action(user_id, "None")
        elif text == "/find":
            await self._find(message, user_id)
        elif text == "/faq":
            await message.answer(PHRASES["FAQMessage"], parse_mode="HTML")
        elif text == "/likes":
            await self._likes(message, user_id)
        else:
            await message.answer("Неизвестная команда. Используй /help.")

    async def _show_profile(self, message: Message, user_id: int):
        user = await self.profile.get_profile(user_id)
        if user and user.name:
            text = self._format_profile(user)
            await message.answer(text, reply_markup=KeyboardFactory.edit_inline(), parse_mode="HTML")
        else:
            await message.answer("Профиль не существует")

    async def _find(self, message: Message, user_id: int):
        city = await self.db.get_field(user_id, "city")
        if not city:
            await message.answer("Вы не указали город поиска. Пожалуйста, заполните анкету.")
            return
        profile = await self.profile.get_unseen_profile(user_id, city)
        if not profile:
            await message.answer("Нет доступных анкет для просмотра в вашем городе.")
            return
        text = self._format_profile_dict(profile)
        await message.answer(text, parse_mode="HTML", reply_markup=KeyboardFactory.view_inline())
        await self.profile.set_action(user_id, f"viewing_{profile['user_id']}")

    async def _likes(self, message: Message, user_id: int):
        likes = await self.db.get_likes_for_user(user_id)
        if not likes:
            await message.answer("У вас нет новых лайков.")
            return
        liked_user_id = likes[0]["user_id"]
        user = await self.db.get_user(liked_user_id)
        if not user:
            await message.answer("Анкета этого пользователя больше недоступна.")
            return
        text = self._format_profile(user)
        await message.answer(text, parse_mode="HTML", reply_markup=KeyboardFactory.view_inline())
        await self.profile.set_action(user_id, f"likes_{liked_user_id}")

    def _format_profile(self, user) -> str:
        name = html.escape(str(user.name or ""))
        age = user.age
        univer = html.escape(str(user.univer or ""))
        about = html.escape(str(user.about or ""))
        requirements = html.escape(str(user.requirements or ""))
        if age:
            if age % 10 == 1 and age % 100 != 11:
                yearword = "год"
            elif age % 10 in [2,3,4] and age % 100 not in [12,13,14]:
                yearword = "года"
            else:
                yearword = "лет"
            return f"<b>{name}</b>, {age} {yearword} | {univer}\n\n<b>О себе: </b>\n<i>{about}</i>\n\n<b>Пожелания к соседу: </b>\n<i>{requirements}</i>\n\n"
        else:
            return f"<b>{name}</b> | {univer}\n\n<b>О себе: </b>\n<i>{about}</i>\n\n<b>Пожелания к соседу: </b>\n<i>{requirements}</i>\n\n"

    def _format_profile_dict(self, data: dict) -> str:
        name = html.escape(str(data.get("name") or ""))
        age = data.get("age")
        univer = html.escape(str(data.get("univer") or ""))
        about = html.escape(str(data.get("about") or ""))
        requirements = html.escape(str(data.get("requirements") or ""))
        if age:
            if age % 10 == 1 and age % 100 != 11:
                yearword = "год"
            elif age % 10 in [2,3,4] and age % 100 not in [12,13,14]:
                yearword = "года"
            else:
                yearword = "лет"
            return f"<b>{name}</b>, {age} {yearword} | {univer}\n\n<b>О себе: </b>\n<i>{about}</i>\n\n<b>Пожелания к соседу: </b>\n<i>{requirements}</i>\n\n"
        else:
            return f"<b>{name}</b> | {univer}\n\n<b>О себе: </b>\n<i>{about}</i>\n\n<b>Пожелания к соседу: </b>\n<i>{requirements}</i>\n\n"