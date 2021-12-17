import requests
from bs4 import BeautifulSoup, Comment

def build_url(gamecode, suffix):
    loc = gamecode[:3]
    url = f'https://www.baseball-reference.com/boxes/{loc}/{gamecode}{suffix}.shtml'
    return url

def scrape_game(gamecode, last_suffix=-1):
    while True:
        last_suffix += 1
        url = build_url(gamecode, last_suffix)
        page = BeautifulSoup(requests.get(url).text, 'lxml')
        if "404" not in page.title.string:
            break
    return scrape_csv(page.body), last_suffix

def scrape_csv(soup):
    # change user agent here?
    #soup = BeautifulSoup(requests.get(url).body)
    comments = soup.find_all(text=lambda t: isinstance(t, Comment))
    table = next(table for comment in comments if (table := BeautifulSoup(comment, 'lxml').find(id="play_by_play")))
    headers = (cell.string for cell in table.select("thead th"))
    to_return = ','.join(headers) + '\n'
    to_return += '\n'.join(
        ','.join(string_recur(child) for child in row.children)
        for row in table.select("tbody tr")
    )
    #for row in table.select("tbody tr"):
    #    to_return += ','.join(string_recur(child) for child in row.children)
    return to_return
    
    #with open(out_filename) as out_file:
    #    writer = csv.writer(out_file, newline='')
    #    writer.write_row(headers)
    #    for row in table.select("tbody tr"):
    #        writer.write_row(string_recur(child) for child in row.children)

def string_recur(elem):
    to_return = ""
    for c in elem.contents:
        try:
            to_return += string_recur(c)
        except AttributeError:
            to_return += c
    return to_return.replace('\xa0', ' ')


