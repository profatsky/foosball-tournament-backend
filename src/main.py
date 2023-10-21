from fastapi import FastAPI
from postgres import pg, migrate, fixture
import uvicorn

app = FastAPI()


@app.on_event('startup')
async def init_db():
    await migrate()


@app.get('/')
async def health():
    return 'server is running!'


@app.get('/fixtures/include')
async def include_fixtures():
    return await fixture()


@app.get('/user/profile')
async def user_profile():
    async with pg:
        return await pg.execute(
            'SELECT user_id, nickname, image_path, created_at from users'
        )


@app.get('/teams/{team_id}')
async def team_info(team_id: int):
    async with pg:
        return {
            "team": await pg.execute(
                'SELECT team_id, title, image_path,'
                ' created_at, first_participant_id, second_participant_id'
                ' from teams where team_id = team_id'
            )
        }


@app.get('/tournaments/{tour_id}')
async def tournaments_info(tour_id: int):
    async with pg:
        return {
            "tour": await pg.execute('SELECT * from tournaments where tour_id = tour_id')
        }


@app.get('/test')
async def test_pg():
    async with pg:
        return await pg.execute('SELECT * from teams')


if __name__ == '__main__':
    # move out to settings
    uvicorn.run(
        'main:app',
        host='127.0.0.1',
        port=8000,
        loop='uvloop',
        reload=True,
        use_colors=True
    )
