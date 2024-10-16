from datetime import datetime
from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTableUUID
from sqlalchemy import Text, DateTime, func, Integer
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped


class Base(DeclarativeBase):
    pass


class User(SQLAlchemyBaseUserTableUUID, Base):
    username: Mapped[str] = mapped_column(Text)
    putty_login: Mapped[str] = mapped_column(Text)
    putty_password: Mapped[str] = mapped_column(Text)


class Device(Base):
    __tablename__ = 'device'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Text, unique=True)
    ip_address: Mapped[str]
    config_file_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
