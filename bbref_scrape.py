from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
#from selenium.webdriver.support.ui import WebDriverWait
#from selenium.webdriver.support import expected_conditions as EC
import selenium
import sys

dropdown_selector = "#play_by_play_sh li.hasmore > span"
button_selector = "#play_by_play_sh li.hasmore li + li + li + li button"
csv_id = "csv_play_by_play"
csv_selector = "#csv_play_by_play"

def debug(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def new_driver():
    options = Options()
    options.headless = True
    options.add_argument('--disable-browser-side-navigation')
    dvr = webdriver.Chrome(options=options)
    dvr.set_page_load_timeout(30)
    return dvr

def main():
    gamecode = sys.argv[1]
    print(bbref_scrape(gamecode, 0)[0])

def bbref_scrape(gamecode, try_from, driver=None):
    if not driver: driver = new_driver()
    # Try until we find the right game (will need multiple attempts for doubleheaders)
    # Usually, games have suffix 0. But, for double (and I presume and greaterheaders) suffices are 1, 2, ...
    while not retrieve_bbref_page(driver, gamecode, try_from):
        debug(f"unable to retrieve {gamecode}{try_from}")
        try_from += 1

    pbp = ''
    button = driver.find_element(by=By.CSS_SELECTOR, value=button_selector)
    driver.execute_script("arguments[0].onclick()", button)
    #driver.execute_script(f"$('{button_selector}').onclick()")
    pbp = "Inn" + driver.find_element(by=By.ID, value=csv_id).text.split("Inn", maxsplit=1)[1]
    #while True:
    #failed = 0
    #for i in range(50):
    #    if show_button(driver) and (pbp := rest(driver)):
    #        break
    #    if i == 49:
    #        debug(f"max tries exceeded: skipping {gamecode}")
    return pbp, try_from

def retrieve_bbref_page(driver, gamecode, suffix):
    loc = gamecode[:3]
    url = f'https://www.baseball-reference.com/boxes/{loc}/{gamecode}{suffix}.shtml'
    retrieve_page(driver, url)
    return "404" not in driver.title

def retrieve_page(driver, url):
    while True:
        try:
            driver.get(url)
            break
        except selenium.common.exceptions.TimeoutException:
            debug(f"{url} exceeded load timeout, retrying...")


def show_button(driver):
    # Scroll to dropdown
    # Trying a whole bunch of things because selenium is super weird and doesn't always get the scrolling right
    dropdown = driver.find_element(by=By.CSS_SELECTOR, value=dropdown_selector)

    # (1) Location_once_scrolling_into_view side effect
    dropdown.location_once_scrolled_into_view
    debug("scrolled location_once_scrolled_into_view")
    try:
        # Hover over dropdown so button appears
        ActionChains(driver).move_to_element(dropdown).perform()
        debug("success location_once_scrolled_into_view")
        return True
    except selenium.common.exceptions.MoveTargetOutOfBoundsException:
        debug("failure location_once_scrolled_into_view")
    #driver.execute_script("arguments[0].scrollIntoViewIfNeeded(true);", dropdown)
    #driver.execute_script(f"$('{dropdown_selector}').scrollIntoView();")

    # (2) ScrollTo pixel location found
    driver.execute_script(f"window.scrollTo(0, {dropdown.location['y']});")
    debug("scrolled scrollTo location")
    try:
        # Hover over dropdown so button appears
        ActionChains(driver).move_to_element(dropdown).perform()
        debug("success scrollTo location")
        return True
    except selenium.common.exceptions.MoveTargetOutOfBoundsException:
        debug("failure scrollTo location")

    # (3) As latch ditch effort, try to scrollBy down a little more
    driver.execute_script("window.scrollBy(0, 150);")
    debug("scrolled scrollBy")
    try:
        # Hover over dropdown so button appears
        ActionChains(driver).move_to_element(dropdown).perform()
        debug("success scrollBy")
        return True
    except selenium.common.exceptions.MoveTargetOutOfBoundsException:
        debug("failure scrollBy")
    return False


def rest(driver):
    # Click button to show CSV
    button = driver.find_element(by=By.CSS_SELECTOR, value=button_selector)
    try:
        button.click()
    except selenium.common.exceptions.ElementNotInteractableException:
        debug("click failed but we'll try to press on anyway")

    # Collect CSV
    csv = ""
    try:
        #csv = driver.find_element(by=By.ID, value=csv_id).text.split("Inn", maxsplit=1)[1]
        csv = driver.find_element(by=By.CSS_SELECTOR, value=csv_selector).text
        debug(csv)
        debug("------")
        csv = csv.split("Inn", maxsplit=1)[1]
    except Exception as e:
        try:
            csv = driver.find_element(by=By.ID, value=csv_id).text.split("Inn", maxsplit=1)[1]
        except Exception as e:
            debug(e)
            return False
    csv = "Inn" + csv
    debug(csv)
    debug("---------")

    return csv
    '''
    # Save CSV
    with open(output_filename, 'w') as out:
        out.write(csv)
    '''

if __name__ == "__main__":
    main()
