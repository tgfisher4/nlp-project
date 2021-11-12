from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bbref_scrape import bbref_scrape, new_driver, retrieve_page

def main():
    import sys
    date = sys.argv[1]
    if len(date) == 4 + 2:
        scrape_month(date)
    elif len(date) == 4 + 2 + 2:
        scrape_day(date, sys.stdout)

bbrefteam = {
    'WSH' : 'WAS',
    'CHC': 'CHN',
    'LAA': 'ANA',
    # fixed: CIN, BOS, CLE, DET, TEX, MIL, OAK, PHI, MIA, SEA, COL, PIT, BAL, HOU, TOR, MIN, ATL, ARI
    'SD': 'SDN',
    'NYY': 'NYA',
    'NYM': 'NYN',
    'CWS': 'CHA',
    'STL': 'SLN',
    'TB': 'TBA',
    'LAD': 'LAN',
    'SF': 'SFN',
    'KC': 'KCA'
}

def scrape_month(yearmonth, driver=None):
    monthfile = open(f'{date}.csv', 'w')
    for day in range(1, 32): 
        scrape_day(f'{yearmonth}{day:2}', monthfile, driver)

def scrape_day(date, outfile, driver=None):
    if not driver: driver = new_driver()
    date_url = 'http://espn.com/mlb/scoreboard/_/date/' + date
    retrieve_page(driver, date_url) # use selenium because the page needs to execute JS to load the relevant data
    games = BeautifulSoup(driver.page_source, 'html.parser').select("#events > article.scoreboard")

    last_suffix = {} # helps manage for doubleheaders (hoping they appear on ESPN and bbref in same order, probably game time
    for game in games:
        if 'fallback' in game['class']: continue # If no recap, skip (no pair to be extracted)
        gameid = game.get('id')
        home = game.select('#teams tr.home span.sb-team-abbrev')[0].text
        away = game.select('#teams tr.away span.sb-team-abbrev')[0].text
     
        bbrefcode = f'{bbrefteam.get(home, home)}{date}'
        pbp, last_suffix[home] = bbref_scrape(bbrefcode, last_suffix.get(home, -1) + 1, driver=driver)

        recap_url = f"https://espn.com/mlb/recap?gameId={gameid}"
        retrieve_page(driver, recap_url)
        recap_pg = BeautifulSoup(driver.page_source, 'html.parser')
        recap = '\n'.join(map(lambda p: p.text, recap_pg.select('div.article-body > p')))
        # Save such that we can find which teams played later (?)
        
        outfile.write(pbp.replace('\n', '\t') + '\n' + recap.replace('\n', '\t') + '\n\n')

if __name__ == "__main__":
    main()
