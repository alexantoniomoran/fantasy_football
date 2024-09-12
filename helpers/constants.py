import os

from helpers.settings import league_id, year

BENCH_SLOT_ID = 20
KEY_PATH = os.path.dirname(os.path.abspath(__file__))

positions_dict = {
    1: "QB",
    2: "RB",
    3: "WR",
    4: "TE",
    5: "K",
    16: "DEF",
}

base_url = f"https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/{year}/segments/0/leagues/{league_id}"
matchup_url = f"{base_url}?view=mMatchup&view=mMatchupScore&scoringPeriodId="
team_url = f"{base_url}?view=mTeam"
