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
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


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
logger = logging.getLogger('glassdoor_scraper')
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
    # {'url': 'https://www.glassdoor.com/Job/united-states-serverless-jobs-SRCH_IL.0,13_IN1_KO14,24.htm',
    #  'country': 'United States'},
    # TODO : United Kingdom (339+)
    # {'url': 'https://www.glassdoor.com/Job/united-kingdom-serverless-jobs-SRCH_IL.0,14_IN2_KO15,25.htm',
    #  'country': 'United Kingdom'},
    # TODO: United Arab Emirates (8+)
    {'url': 'https://www.glassdoor.com/Job/united-arab-emirates-serverless-jobs-SRCH_IL.0,20_IN6_KO21,31.htm',
     'country': 'United Arab Emirates'},
    # TODO: India (1204+)
    # {'url': 'https://www.glassdoor.com/Job/india-serverless-jobs-SRCH_IL.0,5_IN115_KO6,16.htm?sortBy=date_desc',
    #  'country': 'India'},
    # TODO: In case India sites overload and button disappear
    # {'url': 'https://www.glassdoor.com/Job/india-serverless-jobs-SRCH_IL.0,5_IN115_KO6,16.htm',
    #  'country': 'India'},
    # TODO : Australia (107+)
    # 'https://www.glassdoor.com/Job/australia-serverless-jobs-SRCH_IL.0,9_IN16_KO10,20.htm',
    # {'url': 'https://www.glassdoor.com/Job/australia-serverless-jobs-SRCH_IL.0,9_IN16_KO10,20.htm',
    #  'country': 'Australia'},
    # TODO : Singapore (96 +)
    # 'https://www.glassdoor.com/Job/singapore-singapore-serverless-jobs-SRCH_IL.0,19_IC3235921_KO20,30.htm',
    # {'url': 'https://www.glassdoor.com/Job/singapore-singapore-serverless-jobs-SRCH_IL.0,19_IC3235921_KO20,30.htm',
    #  'country': 'Singapore'},
    # TODO: South Africa (24 +)
    # 'https://www.glassdoor.com/Job/south-africa-serverless-jobs-SRCH_IL.0,12_IN211_KO13,23.htm',
    {'url': 'https://www.glassdoor.com/Job/south-africa-serverless-jobs-SRCH_IL.0,12_IN211_KO13,23.htm',
     'country': 'South Africa'},
]

data_pipeline = GlassdoorPostgresPipeline(postgres_db_name="jobglassdoor")

for element in list_of_urls:
    # TODO: Remember to change the country name
    url = element['url']
    country = element['country']
    df = gs.get_jobs(url, 5, data_pipeline, country)
data_pipeline.close_pipeline()

