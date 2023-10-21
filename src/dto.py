from datetime import datetime, UTC

from pydantic import BaseModel, Field


class UserRegistration(BaseModel):
    password: str
    login: str
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


class Tournament(BaseModel):
    tour_id: int
    title: str
    started_at: datetime = Field(default_factory=lambda _: datetime.now(UTC))
    finished_at: datetime = Field(default_factory=lambda _: datetime.now(UTC))
    description: str
    status: str
    winner_team: str | None = None
    winner_id: int | None = None


class CreateTournament(BaseModel):
    title: str
    started_at: datetime
    finished_at: datetime
    description: str
    status: str


class Team(BaseModel):
    team_id: int
    title: str
    image_path: str | None = None
    created_at: datetime
    first_participant_id: int | None = None
    second_participant_id: int | None = None


class Teams(BaseModel):
    team_id: int
    title: str
    image_path: str | None = None
    created_at: datetime
