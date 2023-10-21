from envparse import env

POSTGRES_DSN = env.str('POSTGRES_DSN', default='postgres://postgres:postgres@localhost:5432/foosball')
authjwt_secret_key = env.str('authjwt_secret_key', default=None)
if authjwt_secret_key is None:
    raise RuntimeError(f'environment variable authjwt_secret_key should be set')
