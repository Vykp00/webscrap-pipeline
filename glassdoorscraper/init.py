import glassdoor_job_scraper as gs
from glassdoor_job_pipeline import GlassdoorPostgresPipeline
# For Fake User Agent
import os
import random
import re
import time
from random import randint

import dotenv
import requests
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException, \
    ElementClickInterceptedException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import concurrent.futures

dotenv.load_dotenv(dotenv_path='.env')

# For Selenium Stealth
from selenium_stealth import stealth

MY_API_KEY = os.getenv('MY_SCRAPEOPS_API_KEY')

# ******** CREATE A LOGGER ********
import logging
import sys
from glassdoorscraper.utils import get_user_agent

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
logger = logging.getLogger('__init__')
level = logging.DEBUG
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

list_of_urls = [
    # TODO: United States (800+)
    {'url': 'https://www.glassdoor.com/Job/united-states-serverless-jobs-SRCH_IL.0,13_IN1_KO14,24.htm',
     'country': 'United States'},
    # TODO : United Kingdom (339+)
    {'url': 'https://www.glassdoor.com/Job/united-kingdom-serverless-jobs-SRCH_IL.0,14_IN2_KO15,25.htm',
     'country': 'United Kingdom'},
    # TODO: United Arab Emirates (8+)
    {'url': 'https://www.glassdoor.com/Job/united-arab-emirates-serverless-jobs-SRCH_IL.0,20_IN6_KO21,31.htm',
     'country': 'United Arab Emirates'},
    # TODO: India (1204+)
    {'url': 'https://www.glassdoor.com/Job/india-serverless-jobs-SRCH_IL.0,5_IN115_KO6,16.htm?sortBy=date_desc',
     'country': 'India'},
    # TODO: In case India sites overload and button disappear
    {'url': 'https://www.glassdoor.com/Job/india-serverless-jobs-SRCH_IL.0,5_IN115_KO6,16.htm',
     'country': 'India'},
    # TODO : Australia (107+)
    {'url': 'https://www.glassdoor.com/Job/australia-serverless-jobs-SRCH_IL.0,9_IN16_KO10,20.htm',
     'country': 'Australia'},
    # TODO : Singapore (96 +)
    {'url': 'https://www.glassdoor.com/Job/singapore-singapore-serverless-jobs-SRCH_IL.0,19_IC3235921_KO20,30.htm',
     'country': 'Singapore'},
    # TODO: South Africa (24 +)
    {'url': 'https://www.glassdoor.com/Job/south-africa-serverless-jobs-SRCH_IL.0,12_IN211_KO13,23.htm',
     'country': 'South Africa'},
]


# ********** CONCURRENCY MANAGEMENT ***********
# Executing multiple threads concurrently by mapping through all url
def multithread_scrape(list_of_urls, num_threads=8, retry_limit=3, anti_bot_check=True):
    while len(list_of_urls) > 0:
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            executor.map(lambda element: gs.get_jobs(
                driver, element, 5, data_pipeline, retry_limit=retry_limit, anti_bot_check=anti_bot_check)
                         , list_of_urls)


if __name__ == "__main__":
    # ****** Initializing the webdriver ********
    # Setup Chrome Option (As of now selenium-stealth only support Selenium Chrome.)
    options = Options()

    # Run in headless mode for automated tasks without a visible browser window
    options.add_argument("--headless")
    # Maximize the Chrome window upon startup for an optimized viewport
    options.add_argument('start-maximized')
    # Disable Chrome Extension to ensure a clean automation env
    options.add_argument('--disable-extensions')
    # Disable sandbox mode
    # options.add_argument('--no-sandbox')
    # Disable the use of the /dev/shm shared memory space, addressing potential memory-related issues
    options.add_argument('--disable-dev-shm-usage')

    # Set retry request
    options.set_capability("goog:loggingPrefs", {"performance": "ALL", "browser": "ALL"})

    data_pipeline = GlassdoorPostgresPipeline(postgres_db_name="jobglassdoor")

    for element in list_of_urls:
        # Get Random User Agent
        random_agent = get_user_agent()

        # Set a custom user agent to simulate different browsers or devices for enhanced stealth during automation
        options.add_argument(f'user-agent={random_agent}')

        # Using ChromedriverManager to automatically download and install Chromedriver
        driver = webdriver.Chrome(options=options,
                                  service=Service(ChromeDriverManager().install()))

        # Use Selenium-Stealth to make this browser instance stealthy
        stealth(driver,
                languages=["en-US", "en"],
                vendor="Google Inc.",
                platform="Win32",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True,
                )

        df = gs.get_jobs(driver, element, 5, data_pipeline, anti_bot_check=True)
        driver.quit()
    data_pipeline.close_pipeline()
    data_pipeline = GlassdoorPostgresPipeline(postgres_db_name="jobglassdoor")
    time.sleep(2)
    print('Scraping completed successfully')
