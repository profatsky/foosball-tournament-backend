from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse
from fastapi_jwt_auth import AuthJWT
from fastapi_jwt_auth.exceptions import AuthJWTException

import dto
import exceptions
import settings
from postgres import pg, migrate, UserTable, Tournaments


@asynccontextmanager
async def lifespan(_: FastAPI):
    await migrate()
    yield


app = FastAPI(lifespan=lifespan)


@app.exception_handler(exceptions.ServiceException)
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
    return authorize.get_jwt_subject()


def set_tokens_in_cookies(authorize: AuthJWT, subject: str):
    for token in ['access', 'refresh']:
        created_token = getattr(authorize, f'create_{token}_token')(subject)
        getattr(authorize, f'set_{token}_cookies')(created_token)


@app.post('/registration', response_model=dto.User)
async def register(user: dto.UserRegistration, authorize: AuthJWT = Depends()) -> dto.User:
    async with pg:
        if await UserTable.exists(user.login):
            raise exceptions.BadRequestError('Пользователь с таким логином уже существует')
        created_user = await UserTable.add(user)

    set_tokens_in_cookies(authorize, created_user.login)
    return created_user


@app.post('/login', response_model=dto.User)
async def login(user: dto.UserLogin, authorize: AuthJWT = Depends()) -> dto.User:
    existing = await UserTable.get_by_login(user.login)
    set_tokens_in_cookies(authorize, existing.login)
    return existing


@app.get('/users/me', response_model=dto.User)
async def user_profile(authorize: AuthJWT = Depends()) -> dto.User:
    authorize.jwt_required()
    user_login = authorize.get_jwt_subject()
    async with pg:
        return await UserTable.get_by_login(user_login)


@app.get('/users/{user_id}', response_model=dto.User)
async def user_detail(user_id: int) -> dto.User:
    async with pg:
        return await UserTable.get_by_id(user_id)


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


@app.get('/tournaments', response_model=list[dto.Tournament])
async def show_tournaments():
    async with pg:
        return await Tournaments.get_list()


@app.get('/tournaments/{tour_id}/teams', response_model=list[dto.Teams])
async def show_teams_tournament(tour_id: int):
    async with pg:
        return await Tournaments.get_teams(tour_id)


@app.get('/tournaments/{tour_id}', response_model=dto.Tournament)
async def tournaments_info(tour_id: int):
    async with pg:
        tour: dto.Tournament | None = await Tournaments.get(tour_id)
        if tour is None:
            raise exceptions.NotFoundError("Данного турнира не существует")
        return tour


@app.post('/tournaments/add', response_model=dto.Tournament)
async def add_tournament(tournament: dto.CreateTournament):
    async with pg:
        return await Tournaments.add(tournament)


if __name__ == '__main__':
    uvicorn.run(
        'main:app',
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=settings.DEBUG,
        loop='uvloop',
        use_colors=True
    )
