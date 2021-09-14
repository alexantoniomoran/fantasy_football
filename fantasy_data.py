import pandas as pd

from helpers.constants import (
    fantasy_spreadsheet_id,
    season_overview_tab_name,
    weekly_data_tab_id,
    weekly_data_tab_name,
    winners_data_tab_id,
    winners_data_tab_name,
)
from helpers.google_sheets_funcs import (
    get_sheet_values,
    write_sheet_values,
    write_spreadsheet,
)
from helpers.settings import year
from helpers.utils import (
    get_list_of_scores_by_week_json,
    group_df_by_week_and_position,
    parse_team_json,
    parse_week_json,
)


def build_dataframe(all_players_list):
    columns = ["Team ID", "Team", "Week", "Player", "Position", "Points"]
    df = pd.DataFrame(all_players_list, columns=columns)
    df.to_csv(f"Data/{year}_Season.csv", index=False)

    write_spreadsheet(
        df=df.fillna(""),
        sheet_id=fantasy_spreadsheet_id,
        tab_name=weekly_data_tab_name,
        tab_id=weekly_data_tab_id,
    )

    return df


def write_team_names(df):
    team_names = sorted(df["Team"].drop_duplicates().values.tolist())
    write_sheet_values(
        sheet_id=fantasy_spreadsheet_id,
        range_name=season_overview_tab_name + "!C29:C39",
        values=[[i] for i in team_names],
    )


def read_payout_breakdown():
    read_list = get_sheet_values(
        sheet_id=fantasy_spreadsheet_id,
        range_name=season_overview_tab_name + "!C19:D25",
    )

    price_dict = {}
    for row in read_list:
        price_dict[row[0]] = float(row[1].replace("$", ""))

    return price_dict


def write_group_df(df, price_dict):
    grouped_df = group_df_by_week_and_position(df, price_dict)
    write_spreadsheet(
        df=grouped_df.fillna(""),
        sheet_id=fantasy_spreadsheet_id,
        tab_name=winners_data_tab_name,
        tab_id=winners_data_tab_id,
    )


def main(use_espn_api=False):
    try:
        df = pd.read_csv(f"Data/{year}_Season.csv")
    except:
        use_espn_api = True

    if use_espn_api:
        team_json, week_list = get_list_of_scores_by_week_json()
        team_dict = parse_team_json(team_json)
        all_players_list = parse_week_json(team_dict, week_list)
        df = build_dataframe(all_players_list)

    write_team_names(df)
    price_dict = read_payout_breakdown()
    write_group_df(df, price_dict)


if __name__ == "__main__":
    """
    To Do:
        - Get the playoff teams and write them to C42:C45 automatically
        - Figure out login cookies without selenium so can automate
        - Move to heroku and server job to run hourly
    """

    use_espn_api = True
    main(use_espn_api)
