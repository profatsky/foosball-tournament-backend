import asyncpg
import settings


class PostgresManager:
    def __init__(self, dsn: str | None = None):
        self.dsn: str = dsn or settings.POSTGRES_DSN
        self._pool: asyncpg.Pool = asyncpg.create_pool(dsn)

    async def __aenter__(self):
        self.__connection: asyncpg.Connection = await asyncpg.connect(self.dsn)
        return self.__connection

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.__connection.close()

    async def execute(self, query: str, *args, timeout: int | None = None):
        return await self.__connection.execute(query, *args, timeout=timeout)


pg = PostgresManager()


async def migrate():
    async with pg:
        await pg.execute("""
            create table if not exists users (
                user_id Serial primary key,
                nickname varchar (100) not null,
                image_path text,
                created_at timestamp not null,
                password text not null,
                login text not null 
            );
            
            create table if not exists teams (
                team_id serial primary key,
                title varchar(128) not null,
                image_path text not null,
                created_at timestamp not null,
                first_participant_id integer not null,
                second_participant_id integer not null,
                
                constraint first_participant_fk foreign key (first_participant_id) references users (user_id),
                constraint second_participant_fk foreign key (second_participant_id) references users (user_id)
            );
            
            create table if not exists tournaments (
                tour_id serial primary key,
                title varchar not null,
                started_at timestamp not null,
                finished_at timestamp not null,
                description text not null,
                status varchar not null,
                winner_id integer null,
                
                constraint winner_team_fk foreign key (winner_id) references teams (team_id)
            );
            
            create table if not exists matches (
                match_id serial primary key,
                tour_id integer not null,
                first_team_id integer not null,
                second_team_id integer not null,
                winner_id integer not null,
                parent_id integer null,
                started_at timestamp not null,
                
                constraint tournaments_fk foreign key (tour_id) references tournaments (tour_id) on delete cascade,
                constraint first_team_fk foreign key (first_team_id) references teams (team_id) on delete restrict,
                constraint second_team_fk foreign key (second_team_id) references teams (team_id) on delete restrict,
                constraint winner_team_fk foreign key (winner_id) references teams (team_id) on delete restrict,
                constraint parent_match_fk foreign key (parent_id) references matches (match_id) on delete restrict
            );
            
            create table if not exists tournament_teams (
                team_id integer not null,
                tournament_id integer not null,
                team_number integer not null,
                
                constraint team_fk foreign key (team_id) references teams (team_id) on delete restrict,
                constraint tournament_fk foreign key (tournament_id) references tournaments (tour_id) on delete restrict
            );
        """)
