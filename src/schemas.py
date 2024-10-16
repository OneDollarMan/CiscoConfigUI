import uuid
from datetime import datetime
from fastapi_users import schemas
from pydantic import BaseModel, ConfigDict


class UserRead(schemas.BaseUser[uuid.UUID]):
    username: str
    putty_login: str
    putty_password: str


class UserCreate(schemas.BaseUserCreate):
    username: str
    putty_login: str
    putty_password: str


class UserUpdate(schemas.BaseUserUpdate):
    putty_login: str
    putty_password: str


class DeviceCreate(BaseModel):
    name: str
    ip_address: str


class DeviceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    ip_address: str
    created_at: datetime
    config_file_path: str | None


class DeviceUpdate(BaseModel):
    ip_address: str


class DeviceConfigRead(BaseModel):
    device_name: str
    config_content: str
