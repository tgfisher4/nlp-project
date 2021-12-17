import requests
from bs4 import BeautifulSoup
import json
import html
from pathlib import Path
import os
import traceback
import sys
import time
from datetime import datetime

thirty_days = {9, 4, 6, 11}
headers = {
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36',
    "dnt": '1',
    "sec-ch-ua": '"Google Chrome";v="95", "Chromium";v="95", ";Not A Brand";v="99"',
    "sec-ch-ua-mobile": '?0',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": '1',
    "accept": 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    "accept-encoding": 'gzip, deflate, br',
    "accept-language": 'en-US,en;q=0.9',
    'cache-control': 'no-cache', # hopefully this means we have a better chance for success when previous responses have returned 503
}#{'user-agent': 'espn-{}'.format(os.environ.get('USER', 'cse-40657-fa21'))}

proxies = [ ]

#espn_id2team = {"30": "Rays", "2": "Red Sox", "10": "Yankees", "14": "Blue Jays", "1": "Orioles", "4": "White Sox", "5": "Indians", "6": "Tigers", "7": "Royals", "9": "Twins", "18": "Astros", "12": "Mariners", "11": "Athletics", "3": "Angels", "13": "Rangers", "15": "Braves", "22": "Phillies", "21": "Mets", "28": "Marlins", "20": "Nationals", "8": "Brewers", "24": "Cardinals", "17": "Reds", "16": "Cubs", "23": "Pirates", "26": "Giants", "19": "Dodgers", "25": "Padres", "27": "Rockies", "29": "Diamondbacks"}

mlb_standings_api_fmt = 'https://statsapi.mlb.com/api/v1/standings?leagueId=103,104&season={}&date={}&standingsTypes=regularSeason&hydrate=team'

def main():
    date = sys.argv[1]
    if len(date) == 4 + 2:
        basedir = sys.argv[2] if len(sys.argv) >= 2 else '.'
        scrape_month(int(date[:4]), int(date[-2:]), basedir)
    elif len(date) == 4 + 2 + 2:
        print(scrape_day(date))

def scrape_month(year, month, basedir='.', log_to_file=False):
    # Dang, this is ugly. Done this way to allow access to home/away while storing.
    def store_data_by_teams(data, date, away, home):
        home_dir = os.path.join(basedir, str(year), home["abbrev"])
        Path(home_dir).mkdir(parents=True, exist_ok=True)
        home_file = open(os.path.join(home_dir, date[-4:]), 'w')
        home_file.write(data)
        home_file.close()

        away_dir = os.path.join(basedir, str(year), away["abbrev"])
        Path(away_dir).mkdir(parents=True, exist_ok=True)
        away_file = open(os.path.join(away_dir, date[-4:]), 'w')
        away_file.write(data)
        away_file.close()

    # Called for each game
    def store_data_by_month(data, date, away, home):
        month_file.write(data + '\n')

    failed = 'None'
    year_dir = os.path.join(basedir, str(year))
    Path(year_dir).mkdir(parents=True, exist_ok=True)
    month_file = open(os.path.join(year_dir, f'{month:02}'), 'w')
    for day in range(1, 32 if not month in thirty_days else 31):
        if log_to_file:
            error_dir = os.path.join(basedir, str(year), 'error_logs')
            Path(error_dir).mkdir(parents=True, exist_ok=True)
            error_file = open(os.path.join(error_dir, f'{month:02}{day:02}'), 'w')
            sys.stdout = error_file
        if scrape_day(f'{year}{month:02}{day:02}', store_data_by_month) is False:
            failed = f'{year}{month:02}{day:02}'
    month_file.close()
    return f'{failed} failed.'
            
        
def summarize_half_inning(half_inning, away, home):
    team_and_inning = half_inning.select("header div")[0].text

    # use only team names so we don't have to learn abbrev - name associations
    plays = [e.text.replace(away["abbrev"], away["name"]).replace(home["abbrev"], home["name"]) for e in half_inning.select(".css-accordion .left")]

    # chop off player first initial if present to provide a uniform name format
    #   - there are multi-word last names, but these will appeal wholesale in headlines also
    #   - there are players with the same last name on the same team: these will be ambiguous
    plays = [
        ' '.join(
            word
            #result
            #if not len((parts := result.split(' ', maxsplit=1))[0]) == 1 and not parts[0].endswith('.')
            #else parts[1]
            #for result in play.split(', ')
            for word in play.split(' ') if not (len(word) == 1 or (len(word) == 2 and word.endswith('.')))
        )
        for play in plays if len(play)
    ]
    recap = half_inning.select(".css-accordion .info-row--footer")[0].text

    # Add periods to sentences if not already present.
    summary = ' '.join(s if s.endswith('.') else s + '.' for s in [team_and_inning] + plays + [recap])
    # TODO: end of inning token?
    # summary + ' <EOI> '?
    return summary

class RetryFailed(Exception): pass

def retry(fxn, n_times, expected_err, ident):
    n_try = 0
    for n_try in range(n_times):
        try:
            to_ret = fxn()
            if n_try > 0:
                print(f'[{ident}] Failed {n_try} times, but then worked...')
            return to_ret
        except expected_err as e:
            if n_times == 1 + n_try:
                print(f'[{ident}] Failed {n_times}x ({expected_err.__name__})')
                raise RetryFailed
            time.sleep(10 * (n_try+1)) # backoff
        except Exception as e:
            print(f'[{ident}] Unexcepted exception:')
            print(e)
            print(traceback.format_exc())
            raise RetryFailed

class Retry(Exception): pass

def fetch_page(url):
    page = requests.get(url, headers=headers)
    if page.status_code != 200:
        print(f'[{url}] Got {page.status_code}, not 200')
        raise Retry
    return page

def scrape_pbp(pbp_url, away, home):
    pbp_page = retry(lambda: fetch_page(pbp_url), 3, Retry, pbp_url)
    pbp_soup = BeautifulSoup(pbp_page.text, 'lxml')

    half_innings = pbp_soup.select("#allPlaysContainer section")

    pbp = ' '.join(summarize_half_inning(hi, away, home) for hi in half_innings)
    return pbp


def scrape_standings(standings_url):
    standings_page = retry(lambda: fetch_page(standings_url), 3, Retry, standings_url)
    standings_soup = BeautifulSoup(standings_page.text, 'lxml')

    json_obj = json.loads(standings_page.text)

    standings = {}
    for division in json_obj["records"]:
        for team in division["teamRecords"]:
                # clubName, rather than teamName, avoids undesired abbreviation
                #   (D-backs for Diamondbacks being the motivator here)
                name = team['team']['clubName']
                GB = team['gamesBack']
                # TODO: 
                try:
                    strk = team['streak']['streakCode']
                except KeyError: #streak not present for teams yet to play (April)
                    continue
                standings[name] = {}
                standings[name]['GB'] = GB if GB != "-" else "0.0"
                standings[name]['strk'] = strk[0] + ' ' + strk[1]

    return standings

def scrape_day(date, storage_callback=None):
    date_obj = datetime.strptime(date, "%Y%m%d")
    scoreboard_url = "https://www.espn.com/mlb/scoreboard/_/date/" + date
    try:
        scoreboard_page = retry(lambda: fetch_page(scoreboard_url), 3, Retry, scoreboard_url)
    except RetryFailed as e:
        print(f'[{scoreboard_url}] Skipping {date}...')
        return False

    # Use BeautifulSoup library to parse HTML for dynamic JS data 
    soup = BeautifulSoup(scoreboard_page.content, "lxml")
    scripts = soup.find_all('script')

    # Convert scorebaord to JSON, ignoring ads
    json_obj = {}
    for element in scripts:
        j = str(element)
        j = j[j.find('>')+1:]

        if j.startswith("window.espn.scoreboardData"):
            json_str = j[j.find('{'):j.find('};')+1]
            json_obj = json.loads(json_str)
            break

    standings_url = mlb_standings_api_fmt.format(date_obj.strftime('%Y'), date_obj.strftime('%Y-%m-%d'))
    try:
        standings = scrape_standings(standings_url)
    except RetryFailed as e:
        print(f'[{standings_url}] Skipping {date}...')
        return False

    pbp_to_headlines = []

    events = json_obj['events']

    # Go through all the games
    for event in events:

        # skip non-regular season games (exhibition/spring training/postseason)
        #  - practically, don't have win streak/ gb for these, and want to keep data uniform
        #  - also, theoretically, headlines for postseason probably look different, and don't want to introduce data we don't it to learn.
        if event['season']['slug'] != 'regular-season':
            continue
        try:
            headline = html.unescape(event['competitions'][0]['headlines'][0]['shortLinkText'])
        except KeyError: # Some games don't have a headline: skip these
            print(f"{event['name']} on {date} had no headline/recap available, skipping...")
            continue
        if event['status']['type']['name'] != 'STATUS_FINAL': # Some games were delayed or cancelled: skip these
            #print(event['name'], event['date'][:-7], event['status']['type']['name'])
            print(f"{event['name']} on {date} has status {event['status']['type']['name']}, not STATUS_FINAL, skipping...")
            continue

        try:
            pbp_url = next(filter(lambda l: l['shortText'] == 'Play-by-Play', event['links']))['href']
        except StopIteration: # Some games do not have play-by-plays available: skip
            print(f"{event['name']} on {date} had no play-by-play available, skipping...")
            continue

        try:
            teams = {}
            for team in event['competitions'][0]['competitors']:
                team_info = {
                    "name": team['team']['shortDisplayName'],
                    "abbrev": team['team']['abbreviation'],
                    "score": team['score'],
                    "id": team['team']["id"],
                }
                teams[team['homeAway']] = team_info
            away = teams['away']
            home = teams['home']
        except (KeyError, IndexError):
            print('f[{date}] Team info not in expected format, skipping...')
            return False

        try:
            pbp = scrape_pbp(pbp_url, away, home)
        except RetryFailed as e:
            print(f'[{pbp_url}] Skipping ...')
            continue

        try:
            key_players = {
                ' '.join(player['athlete']['shortName'].split()[1:]):
                player['team']['id']
                for player in event['competitions'][0]['leaders'][0]['leaders']
            }
            away_key_players = [
                player
                for player, team_id in key_players.items()
                if team_id == away["id"]
            ]
            home_key_players = [
                player
                for player, team_id in key_players.items()
                if team_id == home["id"]
            ]
        except KeyError as e:
            print(f'[{date}] Key players not in expected location')
            print(json.dumps(event, indent=2))
            key_players = {}
            home_key_players = away_key_players = []

        header = datetime.strptime(date, "%Y%m%d").strftime("%B %d, %Y.")
        home_key_string = str(home_key_players).replace("'", "") if home_key_players else ''
        away_key_string = str(away_key_players).replace("'", "") if away_key_players else ''
        footer = f'Final: {away["name"]} ({standings[away["name"]]["strk"]}, {standings[away["name"]]["GB"]} GB) {away_key_string + (" " if away_key_string else "")}{away["score"]} - {home["name"]} ({standings[home["name"]]["strk"]}, {standings[home["name"]]["GB"]} GB) {home_key_string + (" " if home_key_string else "")}{home["score"]}.'
        game_summary = ' '.join([header, pbp, footer])
        game_pbp_to_headline = game_summary + '\t' + headline
        pbp_to_headlines.append(game_pbp_to_headline)

        if storage_callback:
            storage_callback(game_pbp_to_headline, date, away, home)

    return '\n'.join(pbp_to_headlines)

if __name__ == "__main__":
    main()
