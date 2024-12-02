import pandas as pd
from day_trawler import day_scores
from play_by_play import scrape_game
from datetime import datetime, timedelta
from get_site import get_site
import time
from typing import Tuple, List, Dict
import csv


def _average(games: List[float]) -> float:
    total: float = 0
    for game in games:
        total += game
    return round(total / len(games), 4)


def _isolate_divisions() -> None:
    games: pd.DataFrame = pd.read_csv("games.csv")
    games = games[~games.iloc[:, :-1].duplicated(keep=False)]
    games.to_csv("games4.csv", index=False)
    return


def _just_do_it(div: int) -> None:
    league: Dict[str, List[List[float]]] = {}
    league_adj: Dict[str, List[List[float]]] = {}
    with open("games4.csv", mode='r') as file:
        csv_reader = csv.reader(file)
        for i, row in enumerate(csv_reader):
            if i == 0:
                continue
            if row[4] != f"{div}.0":
                continue
            home_team: str = row[0]
            away_team: str = row[1]
            if home_team not in league:
                # Initialize with empty lists for each team
                league[home_team] = [[], []]
                league_adj[home_team] = [[], []]
            league[home_team][0].append(float(row[2]))
            league[home_team][1].append(float(row[3]))
            league_adj[home_team][0].append(float(row[2]))
            league_adj[home_team][1].append(float(row[3]))
            if away_team not in league:
                league[away_team] = [[], []]
                league_adj[away_team] = [[], []]
            league[away_team][1].append(float(row[2]))
            league[away_team][0].append(float(row[3]))
            league_adj[away_team][1].append(float(row[2]))
            league_adj[away_team][0].append(float(row[3]))
            for _ in range(50):
                away_adjo: float = _average(league_adj[away_team][0])
                away_adjd: float = _average(league_adj[away_team][1])
                home_adjo: float = _average(league_adj[home_team][0])
                home_adjd: float = _average(league_adj[home_team][1])
                league_adj[away_team][0][-1] = league[away_team][0][-1] / home_adjd
                league_adj[home_team][0][-1] = league[home_team][0][-1] / away_adjd
                league_adj[away_team][1][-1] = league[away_team][1][-1] / home_adjo
                league_adj[home_team][1][-1] = league[home_team][1][-1] / away_adjo
    for _ in range(50):
        game_index: Dict[str, int] = {}
        with open("games4.csv", mode='r') as file:
            csv_reader = csv.reader(file)
            for i, row in enumerate(csv_reader):
                if i == 0:
                    continue
                if row[4] != f"{div}.0":
                    continue
                home_team: str = row[0]
                away_team: str = row[1]
                if home_team not in game_index:
                    game_index[home_team] = 0
                if away_team not in game_index:
                    game_index[away_team] = 0
                for _ in range(50):
                    away_adjo: float = _average(league_adj[away_team][0])
                    away_adjd: float = _average(league_adj[away_team][1])
                    home_adjo: float = _average(league_adj[home_team][0])
                    home_adjd: float = _average(league_adj[home_team][1])
                    league_adj[away_team][0][-1] = league[away_team][0][game_index[away_team]] / home_adjd
                    league_adj[home_team][0][-1] = league[home_team][0][game_index[home_team]] / away_adjd
                    league_adj[away_team][1][-1] = league[away_team][1][game_index[away_team]] / home_adjo
                    league_adj[home_team][1][-1] = league[home_team][1][game_index[home_team]] / away_adjo
                game_index[home_team] += 1
                game_index[away_team] += 1
    finalo : Dict[str, float] = {}
    finald : Dict[str, float] = {}
    final: Dict[str, float] = {}
    for team in league_adj:
        final[team] = round(_average(league_adj[team][0]) - _average(league_adj[team][1]), 4)
        finalo[team] = round(_average(league_adj[team][0]), 4)
        finald[team] = round(_average(league_adj[team][1]), 4)
    final = dict(sorted(final.items(), key=lambda item: item[1], reverse=True))
    finalo = dict(sorted(finalo.items(), key=lambda item: item[1], reverse=True))
    finald = dict(sorted(finald.items(), key=lambda item: item[1], reverse=False))
    with open(f"results{div}.csv", mode='w', newline='') as file:
        writer = csv.writer(file)

        # Write the header (optional)
        writer.writerow(['Key', 'Value'])

        # Write the dictionary data (keys and values)
        for key, value in final.items():
            writer.writerow([key, value, finalo[key], finald[key]])
    for i, team in enumerate(final):
        print(i, team, final[team], finalo[team], finald[team])


def _ppp_est(game_id: int) -> Tuple[float, float]:
    url: str = f"https://stats.ncaa.org/contests/{game_id}/team_stats"
    stats: pd.DataFrame = pd.read_html(get_site(url))[3]
    home: str = list(stats.columns)[2]
    away: str = list(stats.columns)[1]
    col = list(stats.columns)[0]
    for i, stat in enumerate(stats[col]):
        if stat == "FGA":
            FGAH: int = int(stats.at[i, home])
            FGAA: int = int(stats.at[i, away])
        elif stat == "ORebs":
            OrebsH: int = int(stats.at[i, home])
            OrebsA: int = int(stats.at[i, home])
        elif stat == "TO":
            TOH: int = int(stats.at[i, home])
            TOA: int = int(stats.at[i, home])
        elif stat == "FTA":
            FTAH = int(stats.at[i, home])
            FTAA: int = int(stats.at[i, home])
        elif stat == "PTS":
            PTSH = int(stats.at[i, home])
            PTSA: int = int(stats.at[i, home])

    home_ppp = ((FGAH - OrebsH) + TOH + (FTAH * .44)) / PTSH
    away_ppp = ((FGAA - OrebsA) + TOA + (FTAA * .44)) / PTSA
    return round(home_ppp, 2), round(away_ppp, 2)



def _trawl_games() -> None:
    everything : pd.DataFrame = pd.DataFrame()
    for n in [1, 2, 3]:
        print(f"Starting division {n}")
        date: datetime = datetime(2024, 11, 1)
        while True:
            if date.month == 12 and date.day == 2:
                break
            print(date)
            day: pd.DataFrame = day_scores(date, "MBB", division=n)
            everything = pd.concat([everything, day], ignore_index=True)
            date += timedelta(days=1)
            time.sleep(3)
    everything.to_csv("scores.csv")




def _all_games() -> None:
    all_games: pd.DataFrame = pd.read_csv("games.csv")
    failed: int = 0
    for n in [1, 2, 3]:
        index: int = len(all_games)
        print(f"division {n}")
        test_date: datetime = datetime(2024, 12, 2)
        while test_date.day != 2:
            print(test_date)
            day: pd.DataFrame = day_scores(test_date, "MBB", division=n)
            if day.empty:
                test_date += timedelta(days=1)
                time.sleep(3)
                continue
            for i, game_id in enumerate(day["Game_id"]):
                if pd.isna(game_id):
                    continue
                if pd.isna(day["Home_id"][i]):
                    continue
                if pd.isna(day["Away_id"][i]):
                    continue
                print(game_id)
                all_games.at[index, "Home_Team"] = day["Home_Team"][i]
                all_games.at[index, "Away_Team"] = day["Away_Team"][i]
                try:
                    game: pd.DataFrame = scrape_game(game_id)
                except ValueError as e:
                    print(game_id, "not available")
                    continue
                if game.empty:
                    failed += 1
                    time.sleep(3)
                    print(day["Home_Team"][i], ",", day["Away_Team"][i], game_id)
                    ppps: Tuple[float, float] = _ppp_est(game_id)
                    all_games.at[index, "Home_ppp"] = ppps[0]
                    all_games.at[index, "Away_ppp"] = ppps[1]
                    index += 1
                    all_games.at[index, "Division"] = n
                    time.sleep(3)
                    continue
                if game["is_Garbage_Time"].any():
                    cutoff_index = game[game["is_Garbage_Time"] == True].index[0]
                    game = game.loc[:cutoff_index]
                poss: int = game["Poss_Count"].iloc[-1] // 2
                all_games.at[index, "Home_ppp"] = round((game["Home_Score"].iloc[-1] / poss), 2)
                all_games.at[index, "Away_ppp"] = round((game["Away_Score"].iloc[-1] / poss), 2)
                all_games.at[index, "Division"] = n
                index += 1
                time.sleep(3)
            test_date += timedelta(days=1)
            time.sleep(3)
            all_games.to_csv("games.csv", index=False)
    print(index, failed, failed / index)


if __name__ == "__main__":
    # for n in [1, 2, 3]:
    #     _just_do_it(n)
    # _all_games()
    # _isolate_divisions()
    _trawl_games()