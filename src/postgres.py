from functools import wraps
from typing import TypeVar, Type, Any, Iterable, Callable

import asyncpg
from passlib.context import CryptContext
from pydantic import BaseModel

import dto
import settings

DecoratedFunction = TypeVar('DecoratedFunction', bound=Callable[..., Any])
ModelType = TypeVar('ModelType', bound=BaseModel)

password_ctx = CryptContext(schemes=['bcrypt'], deprecated='auto')


def connection_check(function: DecoratedFunction) -> DecoratedFunction:
    @wraps(function)
    async def wrapper(*args, **kwargs):
        if not pg.connected:
            raise RuntimeError('Connection to Postgres is not set!')
        return await function(*args, **kwargs)
    return wrapper


class PostgresManager:
    def __init__(self, dsn: str | None = None):
        self.dsn: str = dsn or settings.POSTGRES_DSN

    @property
    def connected(self) -> bool:
        return bool(self.__connection and not self.__connection.is_closed())

    async def __aenter__(self):
        self.__connection: asyncpg.Connection = await asyncpg.connect(self.dsn)
        return self.__connection

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.__connection.close()

    async def execute(self, query: str, *args, timeout: int | None = None):
        return await self.__connection.execute(query, *args, timeout=timeout)

    async def fetchval(self, query: str, *args, timeout: int | None = None):
        return await self.__connection.fetchval(query, *args, timeout=timeout)

    async def fetchrow(
        self,
        query: str,
        *args,
        timeout: int | None = None,
        record_class: type | None = None
    ):
        return await self.__connection.fetchrow(
            query, *args, timeout=timeout, record_class=record_class
        )

    async def fetch(
        self,
        query: str,
        *args,
        timeout: int | None = None,
        record_class: type | None = None
    ):
        return await self.__connection.fetch(
            query, *args, timeout=timeout, record_class=record_class
        )


pg = PostgresManager()


class Table:
    table: str
    output_model: Type[ModelType]
    input_model: Type[ModelType]

    @classmethod
    @connection_check
    async def _add(cls, data: Any, excluded: Iterable = ()) -> ModelType:
        assert data is not None, 'Wrong data'
        excluded = set(excluded) if excluded else {}

        columns, values = [], []
        for key, val in data.dict().items():
            if key not in excluded:
                columns.append(key)
                values.append(val)

        columns = ', '.join(columns)
        placeholders = ', '.join(f'${i}' for i in range(1, len(values) + 1))

        sql = f'INSERT INTO {cls.table} ({columns}) VALUES ({placeholders}) RETURNING *;'
        record: asyncpg.Record = await pg.fetchrow(sql, *values)
        answer = cls.input_model.parse_obj(dict(record.items()))
        return answer

    @classmethod
    @connection_check
    async def _get(
        cls,
        where: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        order_by: str | None = None,
        single: bool = False
    ) -> list[ModelType] | None | ModelType:
        where_clause = f' WHERE {where}' if where else ''
        order_by_clause = f' ORDER BY {order_by}' if order_by else ''
        limit_clause = f' LIMIT {limit}' if limit else ''
        offset_clause = f' OFFSET {offset}' if offset else ''
        sql = f"""SELECT * from {cls.table}{where_clause}{order_by_clause}{limit_clause}{offset_clause};"""
        records: list[asyncpg.Record] = await pg.fetch(sql)

        answer = []
        for record in records:
            answer.append(cls.output_model.parse_obj(dict(record.items())))

        if single and answer:
            return answer[0]
        elif single and not answer:
            return None

        return answer

    @classmethod
    @connection_check
    async def _update(
        cls,
        data: Any,
        pk: str,
        included: Iterable = (),
        excluded: Iterable = (),
        where: str | None = None,
        single: bool = False,
    ) -> list[ModelType] | None | ModelType:
        data = data.dict()

        included = set(included) if included else {}
        excluded = set(excluded) if excluded else {}

        columns, values = [], []
        for key, val in data.items():
            if (included and key in included) or (not included):
                if key not in excluded and key != pk:
                    columns.append(key)
                    values.append(val)

        columns = ', '.join(columns)
        placeholders = ', '.join(f'${i}' for i in range(1, len(values) + 1))

        if not where:
            match data.get(pk):
                case None:
                    raise ValueError(
                        "Update without 'where' and existent 'pk' value is not possible"
                    )
                case value:
                    where = f"{pk}='{value}'"

        if len(values) > 1:
            columns = f'({columns})'
            placeholders = f'({placeholders})'

        sql = f"""
            UPDATE {cls.table} 
            SET {columns} = {placeholders} 
            WHERE {where} 
            RETURNING *;
        """
        records: list[asyncpg.Record] = await pg.fetch(sql, *values)
        answer = []
        for record in records:
            answer.append(cls.input_model.parse_obj(dict(record.items())))

        if single and answer:
            return answer[0]
        elif single and not answer:
            return None

        return answer

    @classmethod
    @connection_check
    async def _delete(cls, where: str) -> int:
        assert where, '`where` is an obligate parameter'
        sql = f"""DELETE FROM {cls.table} WHERE {where} RETURNING *;"""
        records: list[asyncpg.Record] = await pg.fetch(sql)
        return len(records)


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
            create unique index if not exists login_unique on users(login); 
            create unique index if not exists nickname_unique on users(nickname); 
            
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
                match_uuid text primary key,
                tour_id integer not null,
                first_team_id integer,
                second_team_id integer,
                winner_id integer,
                parent_id integer,
                started_at timestamp not null,
                
                constraint tournaments_fk foreign key (tour_id) references tournaments (tour_id) on delete cascade,
                constraint first_team_fk foreign key (first_team_id) references teams (team_id) on delete restrict,
                constraint second_team_fk foreign key (second_team_id) references teams (team_id) on delete restrict,
                constraint winner_team_fk foreign key (winner_id) references teams (team_id) on delete restrict,
                constraint parent_match_fk foreign key (parent_id) references matches (match_uuid) on delete restrict
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
        await pg.execute(f""" 
        insert into users (
        user_id, nickname, image_path, created_at, password, login
        ) 
        values (
        1, 'Vacilie', '', timestamp '2000-01-01 04:04:04', {UserTable.get_hashed_password('12345')!r}, 'valicie'
        );
        insert into users (
        user_id, nickname, image_path, created_at, password, login
        ) 
        values (
        2, 'Artem', '', timestamp '2000-01-01 04:04:04', {UserTable.get_hashed_password('12345')!r}, 'artem'
        );
        insert into users (
        user_id, nickname, image_path, created_at, password, login
        ) 
        values (
        3, 'Michael', '', timestamp '2000-01-01 04:04:04', {UserTable.get_hashed_password('12345')!r}, 'michael'
        );
        insert into users (
        user_id, nickname, image_path, created_at, password, login
        ) 
        values (
        4, 'Petr', '', timestamp '2000-01-01 04:04:04', {UserTable.get_hashed_password('12345')!r}, 'petr'
        );
        insert into users (
        user_id, nickname, image_path, created_at, password, login
        ) 
        values (
        5, 'Maxim', '', timestamp '2000-01-01 04:04:04', {UserTable.get_hashed_password('12345')!r}, 'maxim'
        );
        insert into users (
        user_id, nickname, image_path, created_at, password, login
        ) 
        values (
        6, 'Valeria', '', timestamp '2000-01-01 04:04:04', {UserTable.get_hashed_password('12345')!r}, 'valeria'
        );
        insert into users (
        user_id, nickname, image_path, created_at, password, login
        ) 
        values (
        7,'Alexandr', '', timestamp '2000-01-01 04:04:04', {UserTable.get_hashed_password('12345')!r}, 'alexandr'
        );
        insert into users (
        user_id, nickname, image_path, created_at, password, login
        ) 
        values (
        8, 'Oleg', '', timestamp '2000-01-01 04:04:04', {UserTable.get_hashed_password('12345')!r}, 'oleg'
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


class UserTable(Table):
    table = 'users'
    input_model = dto.UserRegistration
    output_model = dto.UserLogin

    @classmethod
    def get_hashed_password(cls, password: str) -> str:
        return password_ctx.hash(password)

    @classmethod
    def verify(cls, plain_password: str, hashed_password: str) -> bool:
        return password_ctx.verify(plain_password, hashed_password)

    @classmethod
    async def add(cls, user: dto.UserRegistration) -> dto.UserRegistration:
        user.password = cls.get_hashed_password(user.password)
        return await cls._add(user)

    @classmethod
    @connection_check
    async def exists(cls, login: str, nickname: str) -> bool:
        return bool(
            await pg.fetchval(
                f"""select true from users where login = $1 or nickname = $2""",
                login,
                nickname,
            )
        )
