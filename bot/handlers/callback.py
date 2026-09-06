from aiogram.types import CallbackQuery
from bot.handlers.base import BaseHandler
from bot.services.keyboard import KeyboardFactory
from bot.constants import PHRASES
from regions import Regions  # <--- добавляем импорт
import html

class CallbackHandler(BaseHandler):
    def __init__(self, db, profile, view, bot):
        super().__init__(db, profile, view)
        self.bot = bot

    async def handle(self, callback: CallbackQuery):
        data = callback.data
        user_id = callback.from_user.id
        await callback.answer()

        if data.startswith("reg_"):
            idx = int(data.split("_")[1])
            # Используем список регионов из Regions
            region_keys = list(Regions.keys())
            region = region_keys[idx]  # теперь безопасно
            await self.db.update_field(user_id, "region", region)
            action = await self.profile.get_action(user_id)
            if action == "regionEdit":
                await self.profile.set_action(user_id, "cityEdit")
            else:
                await self.profile.set_action(user_id, "city")
            await callback.message.answer(
                PHRASES["cityMessage"],
                reply_markup=KeyboardFactory.cities_inline(region),
                parse_mode="HTML"
            )
        elif data.startswith("city_"):
            city = data[5:]
            await self.db.update_field(user_id, "city", city)
            action = await self.profile.get_action(user_id)
            if action == "cityEdit":
                await self.profile.set_action(user_id, "None")
                user = await self.profile.get_profile(user_id)
                await callback.message.answer(
                    self._format_profile(user),
                    reply_markup=KeyboardFactory.edit_inline(),
                    parse_mode="HTML"
                )
            else:
                await self.profile.set_action(user_id, "confirm")
                user = await self.profile.get_profile(user_id)
                text = self._format_profile(user)
                await callback.message.answer(
                    PHRASES["confirmMessage"] + text,
                    reply_markup=KeyboardFactory.form_confirm(),
                    parse_mode="HTML"
                )
        elif data.startswith("edit_"):
            field = data[5:]
            if field == "city":
                await self.profile.set_action(user_id, "regionEdit")
                await callback.message.answer(
                    PHRASES["regionMessage"],
                    reply_markup=KeyboardFactory.regions_inline(),
                    parse_mode="HTML"
                )
            else:
                await self.profile.set_action(user_id, f"{field}Edit")
                phrase_key = field + "Message"
                await callback.message.answer(
                    PHRASES.get(phrase_key, "Введите новое значение"),
                    parse_mode="HTML"
                )
        elif data.startswith("view_"):
            reaction = data[5:]
            action = await self.profile.get_action(user_id)
            if action.startswith("likes_"):
                liked_id = int(action.split("_")[1])
                if reaction == "like":
                    mutual, liker_name, liked_name = await self.view.handle_like(user_id, liked_id)
                    if mutual:
                        await self.bot.send_message(
                            liked_id,
                            f"Совпадение с {liker_name}! Свяжитесь чтобы обсудить сожительство!"
                        )
                        await self.bot.send_message(
                            user_id,
                            f"Совпадение с {liked_name}! Свяжитесь чтобы обсудить сожительство!"
                        )
                elif reaction == "report":
                    await self.view.handle_report(user_id, liked_id)
                else:  # dislike
                    await self.view.handle_dislike(user_id, liked_id)
                await callback.message.edit_reply_markup(reply_markup=None)
                if reaction != "like":
                    await self._show_likes(callback.message, user_id)
            elif action.startswith("viewing_"):
                viewed_id = int(action.split("_")[1])
                if reaction == "like":
                    mutual, liker_name, liked_name = await self.view.handle_like(user_id, viewed_id)
                    if mutual:
                        await self.bot.send_message(
                            viewed_id,
                            f"Совпадение с {liker_name}! Свяжитесь чтобы обсудить сожительство!"
                        )
                        await self.bot.send_message(
                            user_id,
                            f"Совпадение с {liked_name}! Свяжитесь чтобы обсудить сожительство!"
                        )
                elif reaction == "report":
                    await self.view.handle_report(user_id, viewed_id)
                else:
                    await self.view.handle_dislike(user_id, viewed_id)
                await self.profile.set_action(user_id, "None")
                await self._find(callback.message, user_id)
        elif data == "accept_rules":
            await self.profile.set_action(user_id, "name")
            await callback.message.edit_text(
                "✅ Правила приняты! Теперь заполним анкету.\n\n" + PHRASES["nameMessage"],
                parse_mode="HTML"
            )
        else:
            await callback.message.answer("Неизвестный callback.")

    # Вспомогательные методы (оставляем без изменений)
    async def _find(self, message, user_id):
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

    async def _show_likes(self, message, user_id):
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
        import html
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
        import html
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