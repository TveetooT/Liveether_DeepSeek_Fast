from dataclasses import dataclass
from typing import Optional

@dataclass
class User:
    user_id: int
    username: Optional[str] = None
    name: Optional[str] = None
    age: Optional[int] = None
    univer: Optional[str] = None
    about: Optional[str] = None
    requirements: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None
    form: bool = False
    action: Optional[str] = None
    root: bool = False
    banned: bool = False
    reports: int = 0
    views_count: int = 0
    created_at: Optional[str] = None
    last_active: Optional[str] = None