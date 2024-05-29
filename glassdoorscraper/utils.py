# ******************************************************************************
#  Copyright (c) 2024. Vy Kauppinen (VyKp00)
# ******************************************************************************
import json
# For Fake User Agent
import os
import random
import re
import sys
import time
from random import randint

import dotenv
import requests
from selenium.webdriver.common.by import By

dotenv.load_dotenv()


MY_API_KEY = os.getenv('MY_SCRAPEOPS_API_KEY')

# ******** CREATE A LOGGER ********
import logging
import sys

# ----------- Logging Level
# Level - Numeric value
# CRITICAL - 50
# ERROR - 40
# WARNING - 30
# INFO - 20
# DEBUG - 10
# NOTSET - 0
# create logger

# Create Logger
logger = logging.getLogger('__utils__')
level = logging.WARNING
logger.setLevel(level)

# Create console handler
c_handler = logging.StreamHandler(stream=sys.stdout)
c_handler.setLevel(level)
#
# # Create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#
# # Add formatter to ch
c_handler.setFormatter(formatter)
#
# # Add ch to logger
logger.addHandler(c_handler)

# Get Random User Agent
def get_user_agent():
    # Send get request to fetch a list of agent
    response = requests.get(f"http://headers.scrapeops.io/v1/user-agents?api_key={MY_API_KEY}")

    # Save the result list
    results_list = response.json()["result"]

    # Choose a random number between 0 and the last index
    random_index = randint(0, len(results_list) - 1)

    # Use random number to pick a random agent
    random_agent = results_list[random_index]
    print("***** New User Agent ***** : ", random_agent)

    return random_agent

# GlassDoor attach job and company id in data-brandviews text. This function is collect the company id
# At this moment, it looks like this "MODULE:n=jsearch-job-listing:eid=680848:jlid=1009289416346"
def fetch_company_id(data):
    # Define a regex pattern to capture the company_id
    pattern = r'eid=(\d+):jlid='

    # Search for the pattern in the text
    match = re.search(pattern, data)

    # Extract the company_id if the pattern is found
    try:
        company_id = match.group(1)
        logger.info(f'CompanyId: {company_id}')
    except:
        logger.warning('ERROR: CompanyId not found')
        company_id = 'NA'

    return company_id


# Retries & Concurrency Management
# The function will enter a while loop that continues until one of three conditions is met:
#
# Scraping is successful.
# The maximum number of retries (retry_limit) is reached.
# An exception occurs that prevents further retries.
def get_status(logs):
    for log in logs:
        if log["message"]:
            d = json.loads(log["message"])
            try:
                content_type = (
                    "text/html"
                    in d["message"]["params"]["response"]["headers"]["content-type"]
                )
                response_received = d["message"]["method"] == "Network.responseReceived"
                if content_type and response_received:
                    return d["message"]["params"]["response"]["status"]
            except:
                pass


# Check if we got anti-bot alert
def passed_anti_bot_check(response):
    if "<title>Security | Glassdoor</title>" in response:
        return False
    return True


# Random Scroller
def random_scroll(driver, min_scroll, max_scroll, scroll_delay):
    """
    Scrolls the web page a small random amount within the specified range to simulate human behavior.

    Args:
    driver (webdriver): The Selenium WebDriver instance.
    min_scroll (int): The minimum number of pixels to scroll.
    max_scroll (int): The maximum number of pixels to scroll.
    scroll_delay (float): The delay in seconds between scroll actions.
    """
    scroll_amount = random.randint(min_scroll, max_scroll)
    driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
    time.sleep(scroll_delay)

# Scroll near the bottom to see "Load More" Button
def scroll_to_near_bottom(driver, min_scroll, max_scroll, scroll_delay):
    # Scroll down near the bottom
    scroll_amount = random.randint(min_scroll, max_scroll)
    driver.execute_script(f"window.scrollTo(0, document.body.scrollHeight - {scroll_amount});")
    time.sleep(scroll_delay)  # Allow time for the page to load more content

    # Check if the 'Load More' button is visible and clickable
    is_button_display = False
    try:
        load_more_button = driver.find_element(By.CSS_SELECTOR, 'button[data-test="load-more"]')
        if load_more_button.is_displayed():
            print("++++++++++Loading Button Founded")
        else:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight - {scroll_amount});")
    except:
        logging.warning("Loading Button Not Found")
