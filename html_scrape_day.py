import requests
from bs4 import BeautifulSoup
import json
from bbref_scrape_comment import scrape_game, string_recur

bbrefteam = {
    'WSH' : 'WAS', # UNNECESSARY COMMENT
    'CHC': 'CHN',
    'LAA': 'ANA',
    # fixed: CIN, BOS, CLE, DET, TEX, MIL, OAK, PHI, MIA, SEA, COL, PIT, BAL, HOU, TOR, MIN, ATL, ARI
    'SD': 'SDN',
    'NYY': 'NYA',
    'NYM': 'NYN',
    'CHW': 'CHA',
    'STL': 'SLN',
    'TB': 'TBA',
    'LAD': 'LAN',
    'SF': 'SFN',
    'KC': 'KCA'
}

def main():
    import sys
    date = sys.argv[1]
    if len(date) == 4 + 2:
        scrape_month(date)
    elif len(date) == 4 + 2 + 2:
        scrape_day(date, sys.stdout)

def scrape_month(yearmonth, basedir='.'):
    monthfile = open(f'{basedir}/{yearmonth}.csv', 'w')
    for day in range(1, 32): 
        scrape_day(f'{yearmonth}{day:2}', monthfile)
    monthfile.close()

def scrape_day(date, outfile):
    # HTTP GET request
    URL = "https://www.espn.com/mlb/scoreboard/_/date/" + date
    page = requests.get(URL)

    # Use BeautifulSoup library to parse HTML for dynamic JS data 
    soup = BeautifulSoup(page.content, "html.parser")
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
    #print(json.dumps(json_obj,indent=2))

    # Go through all the games
    games_list = []
    last_suffix = {} # helps manage for doubleheaders (hoping they appear on ESPN and bbref in same order, probably game time
    for event in json_obj['events']:
        try:
            recap_url = next(filter(lambda l: l['shortText'] == 'Recap', event['links']))['href']
        except StopIteration:
            continue
        if event['status']['type']['name'] != 'STATUS_FINAL':
            print(event['name'], event['date'][:-7], event['status']['type']['name'])
            continue
        #for link in enumerate(event['links']:
        #    if link['shortText'] == 'Recap':
        #        recap_url = link['shortText'][-1]['href']
        #        break
        #    if 
        home = event['competitions'][0]['competitors'][0]["team"]['abbreviation']
        bbrefcode = f'{bbrefteam.get(home, home)}{date}'
        pbp, last_suffix[home] = scrape_game(bbrefcode, last_suffix.get(home, -1))
        recap_soup = BeautifulSoup(requests.get(recap_url).text, 'lxml')
        recap = '\n'.join(
            string_recur(paragraph)
            for paragraph in recap_soup.select("article p")
        )
        outfile.write(pbp.replace('\n', '\t') + '\n' + recap.replace('\n', '\t') + '\n\n')


if __name__ == "__main__":
    main()
