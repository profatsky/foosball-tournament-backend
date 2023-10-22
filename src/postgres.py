from enum import Enum
from functools import wraps
from typing import TypeVar, Type, Any, Iterable, Callable

import asyncpg
from passlib.context import CryptContext
from pydantic import BaseModel

import dto
import exceptions
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
    model: Type[ModelType]

    @classmethod
    @connection_check
    async def _add(cls, data: Any, excluded: Iterable = ()) -> ModelType:
        assert data is not None, 'Wrong data'
        excluded = set(excluded) if excluded else {}

        columns, values = [], []
        for key, val in data.dict().items():
            if key not in excluded:
                columns.append(key)
                if isinstance(val, Enum):
                    values.append(val.value)
                else:
                    values.append(val)

        columns = ', '.join(columns)
        placeholders = ', '.join(f'${i}' for i in range(1, len(values) + 1))

        sql = f'INSERT INTO {cls.table} ({columns}) VALUES ({placeholders}) RETURNING *;'
        record: asyncpg.Record = await pg.fetchrow(sql, *values)
        answer = cls.model.parse_obj(dict(record.items()))
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
            answer.append(cls.model.parse_obj(dict(record.items())))

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
            answer.append(cls.model.parse_obj(dict(record.items())))

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
                image_path text,
                created_at timestamp not null,
                first_participant_id integer not null,
                second_participant_id integer not null,
                
                constraint first_participant_fk foreign key (first_participant_id) references users (user_id),
                constraint second_participant_fk foreign key (second_participant_id) references users (user_id)
            );
            
            create table if not exists tournaments (
                tour_id serial primary key,
                title varchar not null,
                started_at timestamp,
                finished_at timestamp,
                description text not null,
                status varchar not null,
                winner_id integer,
                owner_id integer not null,
                
                constraint user_fk foreign key (owner_id) references users (user_id) on delete restrict,
                constraint winner_team_fk foreign key (winner_id) references teams (team_id)
            );
            
            create table if not exists matches (
                match_uuid text primary key,
                tour_id integer not null,
                first_team_id integer,
                first_team_score integer,
                second_team_id integer,
                second_team_score integer,
                winner_id integer,
                parent_uuid text,
                started_at timestamp not null,
                
                constraint tournaments_fk foreign key (tour_id) references tournaments (tour_id) on delete cascade,
                constraint first_team_fk foreign key (first_team_id) references teams (team_id) on delete restrict,
                constraint second_team_fk foreign key (second_team_id) references teams (team_id) on delete restrict,
                constraint winner_team_fk foreign key (winner_id) references teams (team_id) on delete restrict,
                constraint parent_match_fk foreign key (parent_uuid) references matches (match_uuid) on delete restrict
            );
            
            create table if not exists tournament_teams (
                team_id integer not null,
                tournament_id integer not null,
                team_number integer not null,
                
                constraint team_fk foreign key (team_id) references teams (team_id) on delete restrict,
                constraint tournament_fk foreign key (tournament_id) references tournaments (tour_id) on delete restrict
            );
        """)


class UserTable(Table):
    table = 'users'
    model = dto.User

    @classmethod
    def get_hashed_password(cls, password: str) -> str:
        return password_ctx.hash(password)

    @classmethod
    def verify(cls, plain_password: str, hashed_password: str) -> bool:
        return password_ctx.verify(plain_password, hashed_password)

    @classmethod
    @connection_check
    async def get_by_login(cls, login: str, raise_exception: bool = True) -> dto.UserWithPassword:
        cls.model = dto.UserWithPassword
        user: dto.UserWithPassword | None = await cls._get(where=f'login = {login!r}', single=True)
        cls.model = dto.User
        if user is None and raise_exception:
            raise exceptions.NotFoundError(f'Пользователь с логином: {login!r} не найден.')
        return user

    @classmethod
    @connection_check
    async def get_by_id(cls, user_id: int) -> dto.User:
        user: dto.User | None = await cls._get(where=f'user_id = {user_id}', single=True)
        if user is None:
            raise exceptions.NotFoundError(f'Пользователь с ID: {user_id} не найден.')
        return user

    @classmethod
    @connection_check
    async def add(cls, user: dto.UserRegistration) -> dto.User:
        user.password = cls.get_hashed_password(user.password)
        return await cls._add(user)

    @classmethod
    @connection_check
    async def exists(cls, login: str, nickname: str) -> bool:
        return bool(
            await pg.fetchval(
                f"""select true from users where login = $1 or nickname = $2""",
                login, nickname
            )
        )


class Tournaments(Table):
    table = 'tournaments'
    model = dto.Tournament

    @classmethod
    @connection_check
    async def get_list(cls) -> list[dto.Tournament]:
        # tournaments_records = await pg.fetch(
        #     """
        #         SELECT tour_id, tournaments.title as title, started_at,
        #         finished_at, description, status, teams.title as team_title from tournaments
        #         left join teams on tournaments.winner_id = teams.team_id
        #     """,
        # )
        # return [dto.Tournament.parse_obj(dict(record.items())) for record in tournaments_records]
        return await pg.fetch(
            """
                SELECT tour_id, tournaments.title as title, started_at,
                finished_at, description, status, teams.title as team_title 
                from tournaments 
                left join teams on tournaments.winner_id = teams.team_id
            """,
        )

    @classmethod
    @connection_check
    async def get(cls, tour_id: int) -> dto.Tournament:
        return await pg.fetchrow(
            """
                SELECT tour_id, tournaments.title as title, started_at,
                finished_at, description, status, teams.title as team_title 
                from tournaments 
                left join teams on tournaments.winner_id = teams.team_id
                where tour_id = $1
            """,
            tour_id
        )

    @classmethod
    @connection_check
    async def get_teams(cls, tour_id: int) -> list[dto.Teams]:
        result = await pg.fetch(
            """
            select team_number, title, team_id, created_at 
            from tournament_teams as tour 
            left join teams using(team_id)
            where tournament_id = $1
            """,
            tour_id
        )
        return [dto.Teams.parse_obj(dict(item.items())) for item in result]

    @classmethod
    @connection_check
    async def add(cls, tournament: dto.CreateTournament) -> ModelType:
        return await cls._add(tournament)


class Matches(Table):
    table = 'matches'
    model = dto.UserMatches

    @classmethod
    @connection_check
    async def history_user(cls, user_id) -> list[dto.UserMatches]:
        return await pg.fetch(
            """
            select t.tour_id as tournament_id, t.title as tournament_title,
             m.match_uuid, t1.title as first_team, t2.title as second_team,
              t1.image_path as first_image, t2.image_path as second_image, 
               m.winner_id
            from matches as m 
            join teams as t1 on m.first_team_id = t1.team_id
            join teams as t2 on m.second_team_id = t2.team_id
            join tournaments as t on m.tour_id = t.tour_id
            join users as u on (
            t1.first_participant_id = u.user_id 
            or t1.second_participant_id = u.user_id
            or t2.first_participant_id = u.user_id
            or t2.second_participant_id = u.user_id) 
            where u.user_id = $1 order by m.match_uuid desc
            """,
            user_id
        )
