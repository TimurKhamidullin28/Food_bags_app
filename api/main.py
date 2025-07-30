from typing import List
from fastapi import FastAPI, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from database import engine, async_get_db
from models import Base, User, Token, FoodBag, Booking
from schemas import UserCreateModel, UserOut, FoodBagIn, FoodBagOut, FoodBagUpdate
import utils


app = FastAPI()


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.on_event("shutdown")
async def shutdown(session: AsyncSession = Depends(async_get_db)):
    await session.close()
    await engine.dispose()


@app.post("/signup", response_model=UserOut, tags=["auth"])
async def create_user_account(
    user_data: UserCreateModel,
    session: AsyncSession = Depends(async_get_db),
) -> User:
    """Эндпойнт регистрации нового пользователя по email"""

    db_user = await session.execute(select(User).where(User.email == user_data.email))
    user = db_user.scalar()
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(**user_data.model_dump())
    session.add(new_user)
    await session.commit()

    return new_user


@app.post("/login", tags=["auth"])
async def login_auth_user(
    response: Response,
    auth_user: User = Depends(utils.get_auth_user_username),
    session: AsyncSession = Depends(async_get_db),
) -> dict:
    """Эндпойнт для входа пользователя по имени и паролю (аутентификация)"""

    session_id = utils.generate_session_id()

    new_token = Token(access_token=session_id, user_id=auth_user.id)
    session.add(new_token)
    await session.commit()

    response.set_cookie(utils.COOKIE_SESSION_ID_KEY, session_id)
    return {"result": "ok"}


@app.get("/logout", tags=["auth"])
async def logout_auth_user(
    response: Response,
    user_session_token: Token = Depends(utils.get_session_data),
    session: AsyncSession = Depends(async_get_db),
) -> dict:
    """Эндпойнт для выхода аутентифицированного пользователя"""

    await session.delete(user_session_token)
    await session.commit()

    response.delete_cookie(utils.COOKIE_SESSION_ID_KEY)
    db_user = await session.execute(select(User).where(User.id == user_session_token.user_id))
    user = db_user.scalar()

    return {
        "message": f"Goodbye, {user.name}!",
    }


@app.get("/check", response_model=UserOut, tags=["auth"])
async def check_auth_user(
    user_session_token: Token = Depends(utils.get_session_data),
    session: AsyncSession = Depends(async_get_db),
) -> User:
    """Эндпойнт для проверки текущего пользователя"""

    db_user = await session.execute(select(User).where(User.id == user_session_token.user_id))
    user = db_user.scalar()
    return user


@app.post("/food_bags", tags=["api-owners"])
async def create_food_bag(
    bag_data: FoodBagIn,
    auth_user: User = Depends(utils.get_auth_user_username),
    session: AsyncSession = Depends(async_get_db),
):
    """
    Эндпойнт для создания корзины еды пользователем с ролью "Заведение"
    """

    if auth_user.role == "Клиент":
        raise HTTPException(
            status_code=400,
            detail="Users with the Client role are not allowed to create Food bags",
        )

    new_food_bag = FoodBag(**bag_data.model_dump(), owner=auth_user.id)
    session.add(new_food_bag)
    await session.commit()

    return {"result": "ok"}


@app.delete("/food_bags/{bag_id}", tags=["api-owners"])
async def delete_food_bag(
    bag_id: int,
    auth_user: User = Depends(utils.get_auth_user_username),
    session: AsyncSession = Depends(async_get_db),
):
    """
    Эндпойнт для удаления корзины еды пользователем-владельцем по ее id
    """

    res_food_bag = await session.execute(select(FoodBag).filter(
        FoodBag.id == bag_id, FoodBag.owner == auth_user.id)
    )
    food_bag = res_food_bag.scalar()

    if not food_bag:
        raise HTTPException(
            status_code=400,
            detail="User does not have permission to delete the Food bag",
        )
    await session.delete(food_bag)
    await session.commit()

    return {"result": "ok"}


@app.patch("/food_bags/{bag_id}", tags=["api-owners"])
async def update_food_bag(
    bag_id: int,
    bag_data: FoodBagUpdate,
    auth_user: User = Depends(utils.get_auth_user_username),
    session: AsyncSession = Depends(async_get_db),
):
    """
    Эндпойнт для редактирования корзины еды пользователем-владельцем по ее id
    """

    res_food_bag = await session.execute(select(FoodBag).filter(
        FoodBag.id == bag_id, FoodBag.owner == auth_user.id)
    )
    food_bag = res_food_bag.scalar()

    if not food_bag:
        raise HTTPException(
            status_code=400,
            detail="User does not have permission to update the Food bag",
        )
    if bag_data.name:
        food_bag.name = bag_data.name
    if bag_data.description:
        food_bag.description = bag_data.description
    if bag_data.image:
        food_bag.image = bag_data.image
    if bag_data.price:
        food_bag.price = bag_data.price
    if bag_data.available_bags:
        food_bag.available_bags = bag_data.available_bags
    if bag_data.address:
        food_bag.address = bag_data.address
    if bag_data.until_time:
        food_bag.until_time = bag_data.until_time

    await session.commit()
    await session.refresh(food_bag)

    return {"result": "ok"}


@app.get("/food_bags", response_model=List[FoodBagOut], tags=["api-clients"])
async def get_food_bags_list(
    session: AsyncSession = Depends(async_get_db)
):
    """Эндпойнт для получения списка всех доступных корзин"""

    res_food_bags = await session.execute(select(FoodBag).where(
        FoodBag.available_bags > 0)
    )
    food_bags = res_food_bags.scalars().all()
    return food_bags


@app.get("/food_bags/{bag_id}", tags=["api-clients"])
async def book_food_bag(
    bag_id: int,
    auth_user: User = Depends(utils.get_auth_user_username),
    session: AsyncSession = Depends(async_get_db),
):
    """Эндпойнт для бронирования клиентом корзины еды по ее id"""

    if auth_user.role == "Заведение":
        raise HTTPException(
            status_code=400,
            detail="Only users with the Client role are allowed to book a Food bag",
        )

    res_food_bag = await session.execute(select(FoodBag).where(
        FoodBag.id == bag_id)
    )
    food_bag = res_food_bag.scalar()
    if food_bag:
        food_bag.available_bags -= 1
        new_booking = Booking(user_id=auth_user.id, bag_id=food_bag.id)
        session.add(new_booking)
        await session.commit()

        return {"message": f"User {auth_user.name} has booked a Food bag {food_bag.name}"}
    else:
        raise HTTPException(
            status_code=404,
            detail=f"Food bag with id {bag_id} not found",
        )
