from fastapi import FastAPI
from postgres import pg, migrate
import uvicorn

app = FastAPI()


@app.on_event('startup')
async def init_db():
    await migrate()


@app.get('/')
async def health():
    return 'server is running!'


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
