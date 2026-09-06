from aiogram.types import Message
from bot.handlers.base import BaseHandler
from bot.services.keyboard import KeyboardFactory
from bot.constants import PHRASES, NEXT_ACTION
from config import Config
import html

class MessageHandler(BaseHandler):
    async def handle(self, message: Message):
        text = message.text
        user_id = message.from_user.id
        action = await self.profile.get_action(user_id)

        # Root-код
        if text == Config.ROOT_CODE:
            if await self.db.get_field(user_id, "root") != "true":
                await self.db.update_field(user_id, "root", "true")
                await message.answer(PHRASES["RootCode"], parse_mode="HTML")
                return

        # Кнопки главного меню
        if text in KeyboardFactory.MAIN_BUTTONS.values():
            if text == KeyboardFactory.MAIN_BUTTONS["Profile"]:
                await self.profile.set_action(user_id, "None")
                await self._show_profile(message, user_id)
            elif text == KeyboardFactory.MAIN_BUTTONS["Find"]:
                await self.profile.set_action(user_id, "None")
                await self._find(message, user_id)
            elif text == KeyboardFactory.MAIN_BUTTONS["Likes"]:
                await self.profile.set_action(user_id, "None")
                await self._likes(message, user_id)
            elif text == KeyboardFactory.MAIN_BUTTONS["FAQ"]:
                await message.answer(PHRASES["FAQMessage"], parse_mode="HTML")
            return

        # Возврат
        if text == KeyboardFactory.RETURN_BUTTON:
            await message.answer(PHRASES["Menu"], reply_markup=KeyboardFactory.main_menu(), parse_mode="HTML")
            await self.profile.set_action(user_id, "None")
            return

        # Обработка состояния "правила" – теперь inline-кнопка
        if action == "rules":
            await message.answer(
                "Пожалуйста, примите правила, нажав кнопку ниже.",
                reply_markup=KeyboardFactory.rules_inline(),   # inline-кнопка
                parse_mode="HTML"
            )
            return

        # Обработка состояний анкеты
        if action in ("name", "age", "univer", "about", "requirements", "region", "city", "confirm"):
            await self._process_form_step(message, user_id, action)
            return

        if action in ("nameEdit", "ageEdit", "univerEdit", "aboutEdit", "requirementsEdit", "regionEdit"):
            field = action[:-4]  # убираем "Edit"
            await self._process_edit(message, user_id, field)
            return

        # Если ничего не подошло
        await message.answer("Я не понимаю эту команду. Используй кнопки меню или /help.")

    async def _process_form_step(self, message: Message, user_id: int, action: str):
        text = message.text
        if action == "confirm":
            if text == "Заполнить заново":
                await self.profile.set_action(user_id, "None")
                await self.profile.start_form(user_id)
                await message.answer(PHRASES["nameMessage"], parse_mode="HTML")
            elif text == "Всё хорошо":
                await self.db.update_field(user_id, "form", "true")
                await self.profile.set_action(user_id, "None")
                await message.answer(PHRASES["FormSaved"], parse_mode="HTML")
                await message.answer(PHRASES["Menu"], reply_markup=KeyboardFactory.main_menu(), parse_mode="HTML")
            else:
                await message.answer("Пожалуйста, используй кнопки ниже.", reply_markup=KeyboardFactory.form_confirm())
            return

        ok, error = await self.profile.save_form_data(user_id, action, text)
        if not ok:
            await message.answer(f"⚠️ {error}")
            return

        next_action = NEXT_ACTION.get(action)
        if not next_action:
            await message.answer("Что-то пошло не так. Отправь /form, чтобы начать заново.")
            return

        await self.profile.set_action(user_id, next_action)

        if next_action == "region":
            await message.answer(PHRASES["regionMessage"], reply_markup=KeyboardFactory.regions_inline(), parse_mode="HTML")
        elif next_action == "city":
            region = await self.db.get_field(user_id, "region")
            await message.answer(PHRASES["cityMessage"], reply_markup=KeyboardFactory.cities_inline(region), parse_mode="HTML")
        elif next_action == "confirm":
            user = await self.profile.get_profile(user_id)
            if user:
                text_profile = self._format_profile(user)
                await message.answer(PHRASES["confirmMessage"] + text_profile,
                                     reply_markup=KeyboardFactory.form_confirm(), parse_mode="HTML")
        else:
            phrase_key = next_action + "Message"
            await message.answer(PHRASES.get(phrase_key, "Продолжайте заполнение."), parse_mode="HTML")

    async def _process_edit(self, message: Message, user_id: int, field: str):
        text = message.text
        ok, error = await self.profile.save_form_data(user_id, field, text)
        if not ok:
            await message.answer(f"⚠️ {error}")
            return
        user = await self.profile.get_profile(user_id)
        if user:
            await message.answer(self._format_profile(user), reply_markup=KeyboardFactory.edit_inline(), parse_mode="HTML")
        await self.profile.set_action(user_id, "None")

    # ---------- Вспомогательные методы (одинаковые с CommandHandler) ----------
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