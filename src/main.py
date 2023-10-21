from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi_jwt_auth import AuthJWT
from fastapi_jwt_auth.exceptions import AuthJWTException

import dto
import settings
from postgres import pg, migrate, UserTable, fixture


@asynccontextmanager
async def lifespan(_: FastAPI):
    await migrate()
    yield


app = FastAPI(lifespan=lifespan)


@app.exception_handler(AuthJWTException)
def missing_token_error_handler(_, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message}
    )


@AuthJWT.load_config
def auth_config():
    return [
        ('authjwt_secret_key', settings.authjwt_secret_key),
        ('authjwt_token_location', {'cookies'})
    ]


@app.get('/health')
async def health(authorize: AuthJWT = Depends()):
    authorize.jwt_required()
    return authorize.get_jwt_subject()


def set_tokens_in_cookies(authorize: AuthJWT, subject: str):
    for token in ['access', 'refresh']:
        created_token = getattr(authorize, f'create_{token}_token')(subject)
        getattr(authorize, f'set_{token}_cookies')(created_token)


@app.post('/registration')
async def register(user: dto.UserRegistration, authorize: AuthJWT = Depends()):
    async with pg:
        if await UserTable.exists(user.login, user.nickname):
            return HTTPException(
                status_code=400,
                detail='Пользователь с таким логином или ником уже существует'
            )
        created_user = await UserTable.add(user)

    set_tokens_in_cookies(authorize, created_user.login)
    return created_user


@app.post('/login')
async def login(user: dto.UserLogin, authorize: AuthJWT = Depends()):
    if user.login is None and user.nickname is None:
        return HTTPException(status_code=400, detail="you didn't provide neither login nor nickname")

    set_tokens_in_cookies(authorize, user.login)

    return 'logged in!'


@app.get('/fixtures/include')
async def include_fixtures():
    return await fixture()


@app.get('/user', response_model=list[dto.User])
async def user_profile(authorize: AuthJWT = Depends()):
    authorize.jwt_required()
    user_login = authorize.get_jwt_subject()
    async with pg:
        return await pg.fetch(
            """SELECT user_id, nickname, image_path from users where login = $1""",
            user_login
        )


@app.get('/teams/{team_id}', response_model=dto.Team)
async def team_info(team_id: int):
    async with pg:
        return await pg.fetchrow(
            """
                SELECT team_id, title, image_path, created_at, 
                first_participant_id, second_participant_id
                from teams where team_id = $1
            """,
            team_id
        )


@app.get('/tournaments/{tour_id}', response_model=dto.Tournament)
async def tournaments_info(tour_id: int):
    async with pg:
        return await pg.fetchrow(
            """SELECT * from tournaments where tour_id = $1""",
            tour_id
        )


if __name__ == '__main__':
    uvicorn.run(
        'main:app',
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=settings.DEBUG,
        loop='uvloop',
        use_colors=True
    )
