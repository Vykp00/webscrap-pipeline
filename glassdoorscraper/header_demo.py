from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium import webdriver

import time
import pandas as pd
import requests
from random import randint
import re

# For Fake User Agent
import os
import dotenv
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

dotenv.load_dotenv(dotenv_path='./.env')

# For Selenium Stealth
from selenium_stealth import stealth

MY_API_KEY = os.getenv('MY_SCRAPEOPS_API_KEY')


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


list_of_urls = [
    # US
    'https://www.glassdoor.com/Job/united-states-microservice-jobs-SRCH_IL.0,13_IN1_KO14,26.htm?sortBy=date_desc&jobTypeIndeed=CF3CP',
]


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
        print(f'CompanyId: {company_id}')
    except:
        print('CompanyId not found')
        company_id = 'None'

    return company_id


def get_jobs(url, num_jobs, verbose, slp_time):
    '''Gathers jobs as a dataframe, scraped from Glassdoor'''

    # ****** Initializing the webdriver ********
    # Get Random User Agent
    random_agent = get_user_agent()
    # Setup Chrome Option (As of now selenium-stealth only support Selenium Chrome.)
    options = Options()

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

    driver = webdriver.Chrome(options=options)

    # Use Selenium-Stealth to make this browser instance stealthy
    stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
            )

    # We get url from the list of urls
    driver.get(url)
    jobs = []

    # Click Accept Cookies
    # time.sleep(5)
    cookie_btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable(
        (By.CSS_SELECTOR, 'button#onetrust-accept-btn-handler')))
    cookie_btn.click()
    # time.sleep(2)

    # TODO: Uncommon after testing
    '''
    # Get Total of Job Number
    title_text = driver.find_element(By.TAG_NAME, 'title').text
    # Extract the number part
    number_str = re.sub(r'[^\d]', '', title_text.split()[0])
    num_jobs = int(number_str)
    '''

    # Either Define a fix number of job or collect all
    while len(jobs) < num_jobs:  # If true, should be still looking for new jobs.

        # Let the page load. Change this number based on your internet speed.
        # Or, wait until the webpage is loaded, instead of hardcoding it.
        time.sleep(slp_time)

        # Test for the "Sign Up" prompt and get rid of it.
        '''
        try:
            driver.find_element(By.CSS_SELECTOR, 'body > div.ModalContainer > div.Modal > div.ContentAndBottomSection '
                                                 '> div.ContentSection > div.closeButtonWrapper').click()
            print('Sign up form closed')
        except ElementClickInterceptedException:
            print('Sign up form failed to close')
            pass
        '''

        time.sleep(.1)

        try:
            driver.find_element(By.CLASS_NAME, 'CloseButton').click()  # clicking to the X.
            print(' Sign up x out worked')
        except NoSuchElementException or ElementNotInteractableException:
            print(' Sign up x out failed')
            pass

        # Going through each job in this page
        # job_buttons = driver.find_element(By.CSS_SELECTOR,'ul[aria-label="Jobs List"] a.JobCard_trackingLink__GrRYn')
        job_cards = driver.find_elements(By.CSS_SELECTOR, 'ul[aria-label="Jobs List"] li[data-test="jobListing"]')
        # each job cards have a hyperlink to render the full job card on the right panel
        for job_card in job_cards:

            print("Progress: {}".format("" + str(len(jobs)) + "/" + str(num_jobs)))
            if len(jobs) >= num_jobs:
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

            time.sleep(1)
            collected_successfully = False

            # SomeTimes Sign-up Pop-up open here too
            try:
                driver.find_element(By.CLASS_NAME, 'CloseButton').click()  # clicking to the X.
                print(' Sign up x out worked')
            except NoSuchElementException or ElementNotInteractableException:
                print(' Sign up x out failed')
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
                    # This is why we select li attribute. Because it contains all id
                    job_id = job_card.get_attribute('data-jobid')

                    # Filter company_id from data-brandviews
                    meta_data_raw = job_card.get_attribute('data-brandviews')
                    company_id = fetch_company_id(meta_data_raw)

                    # Company name is in the first h4
                    company_name = job_detail.find_element(By.TAG_NAME, 'h4').text
                    print('Name Done')
                    # Find the job location
                    location = job_detail.find_element(By.CSS_SELECTOR, 'div[data-test="location"]').text
                    print('Location Done')
                    # Job title is in the first h1 element
                    job_title = job_detail.find_element(By.CSS_SELECTOR, 'h1[aria-hidden="false"]').text
                    print('Job Title Done')

                    # Because the description have <p> and <ul>. Fetch all raw content atm
                    job_description = job_detail.find_element(By.XPATH, 'section/div[2]/div[1]').text
                    print('Job Description Done')
                    collected_successfully = True
                except:
                    time.sleep(2)
                    print("Cannot fetch data")

            # Printing for debugging. If you set verbose = True
            if verbose:
                print('Job ID: {}'.format(job_id))
                print('Company ID: {}'.format(company_id))
                print("Job Title: {}".format(job_title))
                print("Job Description: {}".format(job_description[:500]))
                print("Company Name: {}".format(company_name))
                print("Location: {}".format(location))

            # ****************** Company Overview Tab *******************
            # clicking on this:
            # <section class="Section_sectionComponent__nRsB2 JobDetails_jobDetailsSectionContainer__o_x6Z" data-jv-hidden="true">
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

            if verbose:
                print("Size: {}".format(company_size))
                print("Founded: {}".format(company_founded))
                print("Sector: {}".format(company_sector))
                print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")

            jobs.append({
                "Job ID": job_id,
                "Job Title": job_title,
                "Job Description": job_description,
                "Company ID": company_id,
                "Company Name": company_name,
                "Location": location,
                "Size": company_size,
                "Founded": company_founded,
                "Sector": company_sector,
            })
            # add job to jobs

        # Clicking on the "next page" button
        # FIXME: The Code re-scrape the first page. Write a pipelines to remove duplicate data
        try:
            driver.find_element(By.CSS_SELECTOR, 'button[data-test="load-more"]').click()
        except NoSuchElementException:
            print("Scraping terminated before reaching target number of jobs. Needed {}, got {}.".format(num_jobs,
                                                                                                         len(jobs)))
            break

    # quit the driver when we're done
    driver.quit()
    print("Scraping Completed. Close Driver....")
    return pd.DataFrame(jobs)  # This line converts the dictionary object into a pandas DataFrame.
