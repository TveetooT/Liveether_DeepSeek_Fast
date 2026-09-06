from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from regions import Regions

class KeyboardFactory:
    # Тексты кнопок
    MAIN_BUTTONS = {
        "Profile": "👤 Моя анкета",
        "Find": "🔍 Найти сожителя",
        "Likes": "📬 Запросы на сожительство",
        "FAQ": "❓ ЧаВо",
    }
    FORM_BUTTONS = {"Confirm": "Всё хорошо", "Restart": "Заполнить заново"}
    EDIT_BUTTONS = {
        "name": "Изменить имя",
        "age": "Изменить возраст",
        "univer": "Изменить учебное заведение",
        "about": "Изменить описание",
        "requirements": "Изменить пожелания",
        "city": "Изменить город",
    }
    VIEW_BUTTONS = {"like": "👍", "dislike": "👎", "report": "⚠️ Пожаловаться"}
    RETURN_BUTTON = "⬅️ Назад"

    @classmethod
    def main_menu(cls) -> ReplyKeyboardMarkup:
        builder = ReplyKeyboardBuilder()
        for text in cls.MAIN_BUTTONS.values():
            builder.button(text=text)
        builder.adjust(1, 2)
        return builder.as_markup(resize_keyboard=True)

    @classmethod
    def form_confirm(cls) -> ReplyKeyboardMarkup:
        builder = ReplyKeyboardBuilder()
        for text in cls.FORM_BUTTONS.values():
            builder.button(text=text)
        builder.adjust(1, 2)
        return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)

    @classmethod
    def rules_inline(cls) -> InlineKeyboardMarkup:
        """Inline-кнопка для принятия правил"""
        builder = InlineKeyboardBuilder()
        builder.button(text="✅ Принимаю", callback_data="accept_rules")
        return builder.as_markup()

    # (опционально) можно оставить reply-версию, но она не используется
    # @classmethod
    # def rules_reply(cls) -> ReplyKeyboardMarkup:
    #     ...

    @classmethod
    def regions_inline(cls) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        for idx, region in enumerate(Regions.keys()):
            builder.button(text=region, callback_data=f"reg_{idx}")
        builder.adjust(1)
        return builder.as_markup()

    @classmethod
    def cities_inline(cls, region: str) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        for city in Regions.get(region, []):
            builder.button(text=city, callback_data=f"city_{city}")
        builder.adjust(1)
        return builder.as_markup()

    @classmethod
    def edit_inline(cls) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        for key, label in cls.EDIT_BUTTONS.items():
            builder.button(text=label, callback_data=f"edit_{key}")
        builder.adjust(1, 2)
        return builder.as_markup()

    @classmethod
    def view_inline(cls) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        for key, label in cls.VIEW_BUTTONS.items():
            builder.button(text=label, callback_data=f"view_{key}")
        builder.adjust(3)
        return builder.as_markup()

    @classmethod
    def return_button(cls) -> ReplyKeyboardMarkup:
        builder = ReplyKeyboardBuilder()
        builder.button(text=cls.RETURN_BUTTON)
        return builder.as_markup(resize_keyboard=True)