import json
import math
import pandas as pd
import requests

from datetime import datetime

from helpers.constants import (
    BENCH_SLOT_ID,
    matchup_url,
    positions_dict,
    team_url,
)
from helpers.settings import espn_s2_cookie, league_start_date, swid_cookie


def write_json(my_json, filename):
    with open(f"~/Desktop/{filename}.txt", "w") as outfile:
        json.dump(my_json, outfile)


def read_json(filename):
    with open(f"~/Desktop/{filename}.txt") as json_file:
        return json.load(json_file)


def fetch_current_week():
    start_date = datetime.strptime(league_start_date, "%Y-%m-%d")
    current_time = datetime.utcnow()
    days_since_start = max((current_time - start_date).days, 7)
    return min(int(math.ceil(days_since_start / 7.0)), 16)


def get_list_of_scores_by_week_json():
    current_week = fetch_current_week()

    week_list = []
    with requests.session() as session:
        session.cookies.set("swid", swid_cookie)
        session.cookies.set("espn_s2", espn_s2_cookie)

        response = session.get(team_url)
        team_json = response.json()

        for week in range(1, current_week + 1):
            response = session.get(matchup_url + str(week))

            if response.status_code == 200:
                week_list.append(response.json())
            else:
                print(f"Request failed for week {week}")

    return team_json, week_list


def parse_team_json(team_json):
    team_dict = {}
    for team in team_json["teams"]:
        team_dict[team["id"]] = f"{team['location']} {team['nickname']}"

    return team_dict


def _parse_team(week, team, team_dict):
    if "rosterForCurrentScoringPeriod" not in team:
        return []

    team_id = team["teamId"]
    team_owner = team_dict.get(team_id, team_id)
    total_points = team["totalPoints"]
    players = team["rosterForCurrentScoringPeriod"]["entries"]

    player_list = []
    for player in players:
        position = positions_dict.get(
            player["playerPoolEntry"]["player"]["defaultPositionId"], ""
        )
        points = player["playerPoolEntry"]["appliedStatTotal"]
        player_name = player["playerPoolEntry"]["player"]["fullName"]
        if player["lineupSlotId"] != BENCH_SLOT_ID:
            player_list.append(
                [
                    team_id,
                    team_owner,
                    week,
                    player_name,
                    position,
                    points,
                ]
            )

    player_list.append(
        [
            team_id,
            team_owner,
            week,
            "",
            "Total Points",
            total_points,
        ]
    )

    return player_list


def parse_week_json(team_dict, week_list):
    all_players_list = []
    for matchup_json in week_list:
        for matchup in matchup_json["schedule"]:
            week = matchup["matchupPeriodId"]
            for team in ["home", "away"]:
                all_players_list.extend(_parse_team(week, matchup[team], team_dict))

    return all_players_list


def group_df_by_week_and_position(df, price_dict):
    grouped_df_list = []
    for (week, position), data in df.groupby(["Week", "Position"]):
        total_money = price_dict[position]
        max_points = data["Points"].max()

        max_data = data[data["Points"] == max_points]
        split_value = total_money / len(max_data)

        for _, row in max_data.iterrows():
            temp_row = [i for i in row]
            temp_row.append(split_value)
            grouped_df_list.append(temp_row)

    columns = df.columns.values.tolist()
    columns.append("Money Won")
    return pd.DataFrame(grouped_df_list, columns=columns)
