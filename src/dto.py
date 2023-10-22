from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, Extra

import consts


class UserRegistration(BaseModel):
    class Config:
        extra = Extra.allow
    password: str
    login: str
    nickname: str
    image_path: str | None = None


class UserLogin(BaseModel):
    login: str
    password: str


class User(BaseModel):
    user_id: int
    login: str
    nickname: str
    image_path: str | None = None


class Team(BaseModel):
    team_id: int
    title: str
    image_path: str | None = None
    created_at: datetime
    first_participant_id: int | None = None
    second_participant_id: int | None = None


class CreateTeam(BaseModel):
    class Config:
        extra = Extra.allow
    title: str
    image_path: str | None = None
    first_participant_id: int | None = None
    second_participant_id: int | None = None


class Teams(BaseModel):
    team_id: int
    team_number: int
    title: str
    image_path: str | None = None
    created_at: datetime


class UserWithPassword(User):
    password: str


class Tournament(BaseModel):
    tour_id: int
    title: str
    started_at: datetime | None = None
    finished_at: datetime | None = None
    description: str
    status: consts.TournamentStatus
    team_title: str | None = None


class CreateTournament(BaseModel):
    class Config:
        extra = Extra.allow
    title: str
    started_at: datetime | None = Field(default=datetime.now(None))
    finished_at: datetime | None = Field(default=datetime.now(None))
    description: str
    status: consts.TournamentStatus = consts.TournamentStatus.OPENED


class TournamentTeam(Team):
    team_number: int


class Match(BaseModel):
    match_uuid: UUID = Field(default_factory=uuid4)
    tour_id: int
    participants: list[TournamentTeam | None] = Field(default_factory=list)
    winner_id: int | None = None
    parent_uuid: UUID | None = None
    started_at: datetime | None = None


class UserMatches(BaseModel):
    tournament_id: int
    tournament_title: str
    match_uuid: str
    first_team: str
    second_team: str
    winner_id: int | None = None
    first_image: str
    second_image: str
