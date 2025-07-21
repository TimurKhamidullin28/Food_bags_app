from typing import Annotated
import secrets
import uuid

from fastapi import Depends, HTTPException, Cookie
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from database import async_get_db
from models import User, Token


security = HTTPBasic()

COOKIE_SESSION_ID_KEY = "web-app-session-id"


async def get_auth_user_username(
        credentials: Annotated[HTTPBasicCredentials, Depends(security)],
        session: AsyncSession = Depends(async_get_db),
) -> User:
    """Функция для получения пользователя из базы данных по имени"""

    unauth_exc = HTTPException(status_code=401, detail="Invalid username or password")

    db_user = await session.execute(select(User).where(User.name == credentials.username))
    user = db_user.scalar()
    if not user:
        raise unauth_exc

    if not secrets.compare_digest(
        credentials.password.encode("utf-8"),
        user.password.encode("utf-8"),
    ):
        raise unauth_exc
    return user


def generate_session_id() -> str:
    # Функция для генерации случайного токена сессии
    return uuid.uuid4().hex


async def get_session_data(
        session_id: str = Cookie(alias=COOKIE_SESSION_ID_KEY),
        session: AsyncSession = Depends(async_get_db),
) -> Token:
    """Функция для получения токена из базы данных"""

    db_token = await session.execute(select(Token).where(Token.access_token == session_id))
    token = db_token.scalar()
    if not token:
        raise HTTPException(status_code=401, detail="not authenticated")
    return token
