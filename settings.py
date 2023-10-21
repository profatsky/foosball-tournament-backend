from envparse import env

POSTGRES_DSN = env.str('POSTGRES_DSN', default='postgres://postgres:postgres@localhost:5432/foosball')
