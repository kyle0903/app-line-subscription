from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from schema.enums import UserRole

class UserProfile(BaseModel):
    line_id: str
    name: str
    status: int
    role: UserRole
    group_id: UUID
    created_at: datetime
    updated_at: datetime

