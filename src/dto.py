from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class UserRegistration(BaseModel):
    password: str
    login: str
    nickname: str
    image_path: str | None = None
    created_at = datetime.now()


class UserLogin(BaseModel):
    login: str
    password: str


class User(BaseModel):
    user_id: int
    login: str
    nickname: str
    image_path: str | None = None


class UserWithPassword(User):
    password: str


class Tournament(BaseModel):
    tour_id: int
    title: str
    started_at: datetime
    finished_at: datetime
    description: str
    status: str
    winner_id: int | None = None


class Team(BaseModel):
    team_id: int
    title: str
    image_path: str | None = None
    created_at: datetime
    first_participant_id: int | None = None
    second_participant_id: int | None = None


class TournamentTeam(Team):
    team_number: int


class Match(BaseModel):
    match_id: UUID = Field(default_factory=uuid4)
    tour_id: int
    first_team_id: int | None = None
    second_team_id: int | None = None
    winner_id: int | None = None
    parent_uuid: UUID | None = None
    started_at: datetime | None = None
