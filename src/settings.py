from envparse import env

POSTGRES_DSN = env.str('POSTGRES_DSN', default='postgres://postgres:postgres@postgres:5432/foosball')
authjwt_secret_key = env.str('authjwt_secret_key', default=None)
if authjwt_secret_key is None:
    raise RuntimeError(f'environment variable authjwt_secret_key should be set')

# server settings
SERVER_HOST = env.str('SERVER_HOST', default='0.0.0.0')
SERVER_PORT = env.int('SERVER_PORT', default=8000)
DEBUG = env.bool("DEBUG", default=False)
