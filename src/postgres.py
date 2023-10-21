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


async def fixture():
    async with pg:
        await pg.execute(""" 
        insert into users (
        user_id, nickname, image_path, created_at, password, login
        ) 
        values (
        1, 'Vacilie', '', timestamp '2000-01-01 04:04:04', '12345', 'valicie'
        );
        insert into users (
        user_id, nickname, image_path, created_at, password, login
        ) 
        values (
        2, 'Artem', '', timestamp '2000-01-01 04:04:04', '12345', 'artem'
        );
        insert into users (
        user_id, nickname, image_path, created_at, password, login
        ) 
        values (
        3, 'Michael', '', timestamp '2000-01-01 04:04:04', '12345', 'michael'
        );
        insert into users (
        user_id, nickname, image_path, created_at, password, login
        ) 
        values (
        4, 'Petr', '', timestamp '2000-01-01 04:04:04', '12345', 'petr'
        );
        insert into users (
        user_id, nickname, image_path, created_at, password, login
        ) 
        values (
        5, 'Maxim', '', timestamp '2000-01-01 04:04:04', '12345', 'maxim'
        );
        insert into users (
        user_id, nickname, image_path, created_at, password, login
        ) 
        values (
        6, 'Valeria', '', timestamp '2000-01-01 04:04:04', '12345', 'valeria'
        );
        insert into users (
        user_id, nickname, image_path, created_at, password, login
        ) 
        values (
        7,'Alexandr', '', timestamp '2000-01-01 04:04:04', '12345', 'alexandr'
        );
        insert into users (
        user_id, nickname, image_path, created_at, password, login
        ) 
        values (
        8, 'Oleg', '', timestamp '2000-01-01 04:04:04', '12345', 'oleg'
        );
        
        
        insert into teams (
        team_id, title, image_path, created_at, first_participant_id, second_participant_id
        )
         values (
         1, 'Tracking', 'http://dfgvegreg', timestamp '2000-01-01 04:04:04', 1, 2
         );
        insert into teams (
        team_id, title, image_path, created_at, first_participant_id, second_participant_id
        ) 
        values (
        2, 'Frozen', 'http://dfgvegreg', timestamp  '2000-01-01 04:04:04', 3, 4
        );
        insert into teams (
        team_id, title, image_path, created_at, first_participant_id, second_participant_id
        ) 
        values (
        3, 'Poel', 'http://dfgvegreg',  timestamp '2000-01-01 04:04:04', 5, 6
        );
        insert into teams (
        team_id, title, image_path, created_at, first_participant_id, second_participant_id
        ) 
        values (
        4, 'Sila', 'http://dfgvegreg',  timestamp '2000-01-01 04:04:04', 7, 8
        );
        
        insert into tournaments (
        tour_id, title, started_at, finished_at, description, status, winner_id
        )
        values (
        1, 'test1', timestamp '2000-01-01 04:04:04', timestamp '2001-01-01 04:04:04', 'text', 'started', null
        );
        
        insert into matches (
        match_id, tour_id, first_team_id, second_team_id, winner_id, parent_id, started_at
        )
        values (3, 1, 1, 3, 3, null, timestamp '2000-01-01 04:04:04');
        insert into matches (
        match_id, tour_id, first_team_id, second_team_id, winner_id, parent_id, started_at
        ) 
        values (2, 1, 1, 2, 1, 3, timestamp '2000-01-01 04:04:04');
        insert into matches (
        match_id, tour_id, first_team_id, second_team_id, winner_id, parent_id, started_at
        ) 
        values (1, 1, 3, 4, 3, 3, timestamp '2000-01-01 04:04:04');
        
        update tournaments set winner_id = 2 where tour_id = 1;
    """)
    return True
