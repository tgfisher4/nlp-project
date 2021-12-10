import requests
from bs4 import BeautifulSoup
import json
import html

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

def summarize_pbp(pbp_url):
    pbp_soup = BeautifulSoup(requests.get(pbp_url).text, 'lxml')

    away_team = pbp_soup.select(".competitors > .away")[0]
    away = {
        "name": away_team.select(".short-name")[0].text,
        "abbrev": away_team.select(".abbrev")[0].text,
        "score": away_team.select(".score")[0].text
    }

    home_team = pbp_soup.select(".competitors > .home")[0]
    home = {
        "name": home_team.select(".short-name")[0].text,
        "abbrev": home_team.select(".abbrev")[0].text,
        "score": home_team.select(".score")[0].text
    }

    half_innings = pbp_soup.select("#allPlaysContainer section")
    game_summary = ' '.join(summarize_half_inning(hi, away, home) for hi in half_innings)

    game_summary += f' Final score: {away["name"]} {away["score"]} - {home["name"]} {home["score"]}.'
    return game_summary, away, home


def scrape_day(date, outfile):
    # HTTP GET request
    URL = "https://www.espn.com/mlb/scoreboard/_/date/" + date
    page = requests.get(URL)

    # Use BeautifulSoup library to parse HTML for dynamic JS data 
    soup = BeautifulSoup(page.content, "lxml")
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

    # Go through all the games
    for event in json_obj['events']:
        try:
            headline = html.unescape(event['competitions'][0]['headlines'][0]['shortLinkText'])
        except KeyError: # Some games don't have a headline: skip these
            continue
        if event['status']['type']['name'] != 'STATUS_FINAL': # Some games were delayed or cancelled: skip these
            #print(event['name'], event['date'][:-7], event['status']['type']['name'])
            continue

        pbp_url = next(filter(lambda l: l['shortText'] == 'Play-by-Play', event['links']))['href']
        game_summary, away, home = summarize_pbp(pbp_url)

        outfile.write(game_summary + '\t' + headline + '\n')

if __name__ == "__main__":
    main()
