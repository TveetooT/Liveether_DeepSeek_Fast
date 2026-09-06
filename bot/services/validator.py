from typing import Tuple, Optional, Any

class Validator:
    FIELD_LIMITS = {
        "name": (1, 50),
        "univer": (1, 100),
        "about": (1, 1000),
        "requirements": (1, 1000),
    }
    AGE_MIN, AGE_MAX = 16, 100

    @classmethod
    def validate_field(cls, action: str, raw_text: Optional[str]) -> Tuple[bool, Optional[str], Any]:
        if raw_text is None:
            return False, "Пожалуйста, отправь текстовое сообщение (не фото, не стикер и т.п.).", None
        text = raw_text.strip()
        if action == "age":
            try:
                age = int(text)
            except ValueError:
                return False, "Возраст должен быть числом, например: 22", None
            if age < cls.AGE_MIN or age > cls.AGE_MAX:
                return False, f"Укажи реальный возраст (от {cls.AGE_MIN} до {cls.AGE_MAX} лет).", None
            return True, None, age
        if action in cls.FIELD_LIMITS:
            min_len, max_len = cls.FIELD_LIMITS[action]
            if len(text) < min_len:
                return False, "Поле не может быть пустым.", None
            if len(text) > max_len:
                return False, f"Слишком длинно — не больше {max_len} символов (сейчас {len(text)}).", None
            if action in ("name", "univer"):
                if '\n' in text or '\r' in text or '\t' in text:
                    return False, "Использование переноса строки и табуляции запрещено. Введите текст в одну строку.", None
            return True, None, text
        return True, None, text