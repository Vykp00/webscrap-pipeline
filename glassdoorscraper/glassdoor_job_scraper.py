# ******************************************************************************
#  Copyright (c) 2024. Vy Kauppinen (VyKp00)
# ******************************************************************************
# For Fake User Agent
import os
import re
import time

import dotenv
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException, \
    ElementClickInterceptedException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

dotenv.load_dotenv(dotenv_path='./.env')

# For Selenium Stealth
from selenium_stealth import stealth

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

# Get utils
from utils import get_user_agent, random_scroll, fetch_company_id, scroll_to_near_bottom


# Sometimes there's broken job card so refreshing doesn't help
def card_is_broken(driver):
    try:
        # Try finding the 'Reload' button
        button_2 = driver.find_element(By.XPATH,
                                       '//*[@id="app-navigation"]/div[3]/div[2]/div[2]/div/div[1]/div/button')
        logger.warning("Reload Button Found: That Job Card is Broken.")
        return True
    except NoSuchElementException:
        logger.warning("Reload Button not Found. Different Issues")
        return False


def get_jobs(url, slp_time, data_pipeline, country):
    '''Gathers jobs, scraped from Glassdoor'''
    print("Scraping start.....................")

    # TODO: Transfer to init.py
    # ****** Initializing the webdriver ********
    # Get Random User Agent
    random_agent = get_user_agent()
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

    # Wait for the page to load
    # TODO: Make alternatives for time.sleep() as it's not recommended for production
    driver.set_page_load_timeout(10)

    # We get url from the list of urls
    driver.get(url)

    # The set of collected jobs to prevent duplicates
    collected_job_ids = set()

    # Click Accept Cookies
    try:
        cookie_btn = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, 'button#onetrust-accept-btn-handler')))
        cookie_btn.click()
    except:
        logger.warning("Cannot find Accept Cookies button")
        pass

    # Get Total of Job Number
    time.sleep(1)
    try:
        title_text = driver.find_element(By.CSS_SELECTOR, 'h1[data-test="search-title"]').text
        print(title_text)
    except NoSuchElementException:
        title_text = None
        print("ERROR: Cannot find title")
        pass

    if title_text:
        # Ensure title_text is not empty and contains at least one space
        if len(title_text.split()) > 0:
            # Extract the number part
            number_str = re.sub(r'[^\d]', '', title_text.split()[0])
            if number_str:
                real_num_jobs = int(number_str)
                num_jobs = real_num_jobs
                print("Total of search job results: {}".format(real_num_jobs))
            else:
                print("No numeric value found in the title text")
        else:
            print("Title text does not contain the expected format")
    else:
        num_jobs = 50
        print("Title text is None or empty. Use default num_jobs as 50")

    # Either Define a fix number of job or collect all
    # ******************* MAIN LOOP *************
    while len(collected_job_ids) < num_jobs:  # If true, should be still looking for new jobs.

        # Let the page load. Change this number based on your internet speed.
        # Or, wait until the webpage is loaded, instead of hardcoding it.
        time.sleep(slp_time)

        # Test for the "Sign Up" prompt and get rid of it.
        time.sleep(.1)

        try:
            driver.find_element(By.CLASS_NAME, 'CloseButton').click()  # clicking to the X.
            print(' Sign up x out worked')
        except NoSuchElementException or ElementClickInterceptedException:
            print(' Sign up x out failed')
            pass

        # Going through each job in this page
        # job_buttons = driver.find_element(By.CSS_SELECTOR,'ul[aria-label="Jobs List"] a.JobCard_trackingLink__GrRYn')
        job_cards = driver.find_elements(By.CSS_SELECTOR, 'ul[aria-label="Jobs List"] li[data-test="jobListing"]')
        # each job cards have a hyperlink to render the full job card on the right panel
        for job_card in job_cards:
            # This is why we select li attribute. Because it contains all id
            # Fetch the job's id and cross-checking with collected ones
            # NOTE: THIS IS ONLY CHECK WHEN THIS FUNCTION RUN. UNLIKE DATABASE CHECK
            try:
                job_id = job_card.get_attribute('data-jobid')
            except:
                print('ERROR: Cannot find job ID. Something is wrong!!!')
                continue

            just_refresh = False

            # If job id exists already, skip it
            if job_id in collected_job_ids:
                # print('Job Id Has Been Scraped. Drop This: {}'.format(job_id))
                # Only print when it hit the point of refresh
                if just_refresh:
                    print('Drop this: {}'.format(job_id))
                continue

            # Perform a small random scroll
            random_scroll(driver, min_scroll=50, max_scroll=200, scroll_delay=1)

            print("---------Progress: {}----------".format("" + str(len(collected_job_ids)) + "/" + str(num_jobs)))
            if len(collected_job_ids) >= num_jobs:
                break

            # Find the job button in the job card

            try:
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable(job_card)).click()
                # job_card.click()
                print("Click Job Card Work")
                # time.sleep(5)
            except:
                print("Click Job_Card")
                pass

            try:
                div_card = WebDriverWait(job_card, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, 'div.jobCard')))
                div_card.click()
                print("Click Div_Card Work")
            except:
                print("Click Div_card Failed")
                pass

            time.sleep(2)  # Wait for the page to render
            collected_successfully = False

            # SomeTimes Sign-up Pop-up open here too
            try:
                driver.find_element(By.CLASS_NAME, 'CloseButton').click()  # clicking to the X.
                print(' Sign up x out worked')
            except NoSuchElementException or ElementNotInteractableException:
                print(' Sign up x out failed')
                pass

            # Sometimes the Show More button doesn't show
            try:
                # Click 'Show More' Button to expands
                show_more_btn = WebDriverWait(driver, 4).until(
                    EC.element_to_be_clickable(
                        (By.XPATH,
                         '//*[@id="app-navigation"]/div[3]/div[2]/div[2]/div/div[1]/section/div[2]/div[2]/button[@aria-expanded="false"]')))
                show_more_btn.click()
                time.sleep(2)
                print('-------Click Show More Worked----------')
            except:
                print('------Show More Button Click Failed Or Disappear--------')
                pass

            while not collected_successfully:
                # ************ Fetch Job Information *************
                try:
                    # Focus all search element in the JobDetails div. This line fetch div.JobDetails_jobDetailsContainer__y9P3L
                    # This ensures we only fetch elements from the job details container
                    job_detail = driver.find_element(By.XPATH,
                                                     '//*[@id="app-navigation"]/div[3]/div[2]/div[2]/div/div[1]')

                    # Make it a bit human. Click on the box
                    WebDriverWait(driver, 10).until(EC.element_to_be_clickable(job_detail)).click()

                    print("Click Job Detailed Work")

                    # Filter company_id from data-brandviews
                    meta_data_raw = job_card.get_attribute('data-brandviews')
                    company_id = fetch_company_id(meta_data_raw)
                    logger.debug('Company ID done')

                    # Company name is in the first h4
                    company_name = job_detail.find_element(By.TAG_NAME, 'h4').text
                    logger.debug('Comp Name done')

                    # Find the job location
                    location = job_detail.find_element(By.CSS_SELECTOR, 'div[data-test="location"]').text
                    logger.debug('Location Done')

                    # Job title is in the first h1 element
                    job_title = job_detail.find_element(By.CSS_SELECTOR, 'h1[aria-hidden="false"]').text
                    logger.debug('Job Title Done')

                    # Because the description have <p> and <ul>. Fetch all raw content atm
                    job_description = job_detail.find_element(By.XPATH, 'section/div[2]/div[1]').text
                    logger.debug('Job Description Done')

                    # Get job relative url to recheck data easily
                    job_url = job_card.find_element(By.CSS_SELECTOR, 'a[data-test="job-link"]').get_attribute('href')
                    logger.debug('URL Done')
                    collected_successfully = True
                except:
                    time.sleep(2)
                    # If that job card is broken, Try skipping to the next job
                    if card_is_broken(driver):
                        logger.warning("That Card is broken....")
                        company_id = -1
                        company_name = -1
                        location = -1
                        job_title = -1
                        job_description = -1
                        job_url = -1
                        collected_successfully = True
                    else:
                        try:
                            next_btn = WebDriverWait(driver, 10).until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-test="load-more"]')))
                            next_btn.click()
                            time.sleep(2)
                            logger.warning("Cannot fetch data. Try Clicking Next Button")
                        except:
                            logger.warning("Waiting Time Out... Skip this card")
                            company_id = -1
                            company_name = -1
                            location = -1
                            job_title = -1
                            job_description = -1
                            job_url = -1
                            collected_successfully = True

            # Printing for debugging. If you set verbose = True
            logger.debug('Job ID: {}'.format(job_id))
            logger.debug('Company ID: {}'.format(company_id))
            logger.debug("Job Title: {}".format(job_title))
            logger.debug("Job Description: {}".format(job_description[:500]))
            logger.debug("Company Name: {}".format(company_name))
            logger.debug("Location: {}".format(location))
            logger.debug("Job URL: {}".format(job_url))

            # ****************** Company Overview Tab ******************* clicking on this: <section
            # class="Section_sectionComponent__nRsB2 JobDetails_jobDetailsSectionContainer__o_x6Z"
            # data-jv-hidden="true">
            try:
                # Here we fetch information about company such as size, year company_founded, sector
                company_card = job_detail.find_element(By.CSS_SELECTOR, 'section[data-jv-hidden="true"]')
                company_card.click()

                try:
                    company_size = company_card.find_element(By.CSS_SELECTOR,
                                                             'div > div > div:nth-child(1) > div').text
                except NoSuchElementException:
                    company_size = 'NA'

                try:
                    company_founded = company_card.find_element(By.CSS_SELECTOR,
                                                                'div > div > div:nth-child(2) > div').text
                except NoSuchElementException:
                    company_founded = 'NA'

                try:
                    company_sector = company_card.find_element(By.CSS_SELECTOR,
                                                               'div > div > div:nth-child(5) > div').text
                except NoSuchElementException:
                    company_sector = 'NA'

            except NoSuchElementException:  # Rarely, some job postings do not have the "Company" tab.
                company_size = 'NA'
                company_founded = 'NA'
                company_sector = 'NA'

            logger.debug("Size: {}".format(company_size))
            logger.debug("Founded: {}".format(company_founded))
            logger.debug("Sector: {}".format(company_sector))
            logger.debug("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")

            # add job to data pipeline. Makesure you call it
            # If this card is not broken
            if company_id == -1:
                print('>>>>>>>>>> Skip the broken job card: ', job_id)
            else:
                data_pipeline.add_job({
                    "job_id": job_id,
                    "job_title": job_title,
                    "job_description": job_description,
                    "company_id": company_id,
                    "company_name": company_name,
                    "job_url": job_url,
                    "job_location": location,
                    "company_size": company_size,
                    "founded_year": company_founded,
                    "company_sector": company_sector,
                    "country": country,
                })
            # Added successfully collected job to collected job id lists
            # Also the broken one to avoid it
            collected_job_ids.add(job_id)

        # Clicking on the "next page" button
        scroll_to_near_bottom(driver, 20, 80, 1.5)
        button_clicked = False
        while not button_clicked:
            try:
                # Wait for the 'Load More' button to be visible
                load_more_button = WebDriverWait(driver, 10).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, 'button[data-test="load-more"]'))
                )
                # Click the 'Load More' button
                load_more_button.click()
                # Wait for the new content to load
                time.sleep(2)
                button_clicked = True

            except:
                # If we still have missing collected data
                if len(collected_job_ids) < num_jobs:
                    logger.warning("Reload ERROR. Load More Button disappear. Scraping terminated before reaching "
                                   "target number of jobs. Needed {}, got {}.".format(num_jobs, len(collected_job_ids)))
                    button_space_element = driver.find_element(By.CSS_SELECTOR, 'div.JobsList_wrapper__EyUF6')
                    # TODO: Take screenshot of full page instead
                    # button_space_element.screenshot(f'load-more-button-error-{country}.png')
                    time.sleep(0.5)
                else:
                    print(
                        "No More Page. Needed {}, got {}.".format(num_jobs, len(collected_job_ids)))
                break

    print("Scraping Completed. Closing Driver....")
    time.sleep(2)
    # quit the driver when we're done
    driver.quit()
    # return pd.DataFrame(jobs)  # This line converts the dictionary object into a pandas DataFrame.
