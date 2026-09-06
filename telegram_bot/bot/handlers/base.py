from abc import ABC, abstractmethod
from aiogram.types import Message, CallbackQuery
from bot.services.database import DatabaseService
from bot.services.keyboard import KeyboardFactory
from bot.services.profile import ProfileService
from bot.services.view import ViewService

class BaseHandler(ABC):
    def __init__(self, db: DatabaseService, profile_service: ProfileService, view_service: ViewService):
        self.db = db
        self.profile = profile_service
        self.view = view_service
        self.kb = KeyboardFactory

    @abstractmethod
    async def handle(self, event):
        pass