import math
import random

import dto


class TournamentBracket:
    def __init__(self, tour_id: int, teams: list[dto.Team]):
        self.tour_id = tour_id
        random.shuffle(teams)
        self.teams = self._number_the_teams_within_tournament(teams)
        self.teams_length = len(teams)
        self.matches = []

    def get_matches(self) -> list[dto.Match]:
        self._create_matches()
        return self.matches

    @staticmethod
    def _number_the_teams_within_tournament(teams: list[dto.Team]) -> list[dto.TournamentTeam]:
        return [dto.TournamentTeam(**teams[i].__dict__, team_number=i + 1) for i in range(len(teams))]

    @staticmethod
    def _get_team_with_max_team_number(teams: list[dto.TournamentTeam]):
        max_num = 0
        team_with_max_team_number = None
        for team in teams:
            if team is not None and team.team_number > max_num:
                max_num = team.team_number
                team_with_max_team_number = team
        return team_with_max_team_number

    @staticmethod
    def _get_team_by_team_number(teams: list[dto.TournamentTeam], team_num: int):
        for team in teams:
            if team is not None and team.team_number == team_num:
                return team

    def _divide_teams(self) -> list[dto.TournamentTeam | None]:
        divided_teams = [self.teams[0]]
        temp: list[dto.Team | None] = self.teams[1:]
        count = 0

        for i in range(0, int(2 ** math.ceil(math.log(self.teams_length, 2)) - self.teams_length)):
            temp.append(None)

        for _ in range(0, int(math.ceil(math.log(self.teams_length, 2)))):
            team_with_max_tournament_number = self._get_team_with_max_team_number(divided_teams)
            max_tournament_number = team_with_max_tournament_number.team_number
            for i in range(len(divided_teams)):
                index = divided_teams.index(team_with_max_tournament_number) + 1
                divided_teams.insert(index, temp[count])

                max_tournament_number -= 1
                team_with_max_tournament_number = self._get_team_by_team_number(divided_teams, max_tournament_number)
                count += 1

        return divided_teams

    def _create_matches(self):
        divided_teams = self._divide_teams()

        # Создание матчей для первого раунда. Команды, у которых нет соперников,
        # не прикрепляются к матчам до тех пор, пока не будут сформированы матчи следующих раундов,
        # где этим командам будет найден соперник
        first_round: list[dto.Match | dto.TournamentTeam] = []
        for n in range(0, len(divided_teams), 2):

            # Если после команды в списке следует None, значит у команды нет соперника
            if divided_teams[n + 1] is None:
                first_round.append(divided_teams[n])

            else:
                # Создание матча с двумя рядом стоящим в списке командами
                match = dto.Match(
                    tour_id=self.tour_id,
                    first_team_id=divided_teams[n].team_id,
                    second_team_id=divided_teams[n + 1].team_id
                )
                first_round.append(match)
                self.matches.append(match)

        self._create_matches_after_first_round(first_round)

    def _create_matches_after_first_round(self, items: list[dto.TournamentTeam | dto.Match]):
        if len(items) == 1:
            return

        matches_on_current_round: list[dto.Match] = []
        for i in range(0, len(items), 2):

            match = dto.Match(
                tour_id=self.tour_id
            )

            if isinstance(items[i], dto.TournamentTeam):
                match.first_team_id = items[i].team_id
            else:
                items[i].parent_uuid = match.match_id

            if isinstance(items[i + 1], dto.TournamentTeam):
                match.second_team_id = items[i + 1].team_id
            else:
                items[i + 1].parent_uuid = match.match_id

            matches_on_current_round.append(match)
            self.matches.append(match)

        self._create_matches_after_first_round(matches_on_current_round)
