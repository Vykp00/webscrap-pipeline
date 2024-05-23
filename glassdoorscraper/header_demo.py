# ******************************************************************************
#  Copyright (c) 2024. Vy Kauppinen (VyKp00)
# ******************************************************************************

# For Fake User Agent
import os
import re
import time
from random import randint

import dotenv
import requests
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

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
        print('ERROR: CompanyId not found')
        company_id = 'NA'

    return company_id


def get_jobs(url, verbose, slp_time, data_pipeline):
    '''Gathers jobs, scraped from Glassdoor'''
    print("Scraping start.....................")

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
    #jobs = []

    # The set of collected jobs to prevent duplicates
    collected_job_ids = set()

    # Click Accept Cookies
    # Wait for the page to load
    time.sleep(slp_time)

    cookie_btn = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
        (By.CSS_SELECTOR, 'button#onetrust-accept-btn-handler')))
    cookie_btn.click()

    # TODO: Reimplement it after pipeline
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
    while len(collected_job_ids) < num_jobs:  # If true, should be still looking for new jobs.

        # Let the page load. Change this number based on your internet speed.
        # Or, wait until the webpage is loaded, instead of hardcoding it.
        time.sleep(slp_time)

        # Test for the "Sign Up" prompt and get rid of it.
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
            # This is why we select li attribute. Because it contains all id
            # Fetch the job's id and cross-checking with collected ones
            # NOTE: THIS IS ONLY CHECK WHEN THIS FUNCTION RUN. UNLIKE DATABASE CHECK
            try:
                job_id = job_card.get_attribute('data-jobid')
            except:
                print('ERROR: Cannot find job ID. Something is wrong!!!')
                continue

            # If job id exists already, skip it
            if job_id in collected_job_ids:
                print('Job Id Has Been Scraped. Drop This: {}'.format(job_id))
                continue

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

            time.sleep(1)
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
                    print('Company ID done')

                    # Company name is in the first h4
                    company_name = job_detail.find_element(By.TAG_NAME, 'h4').text
                    print('Comp Name done')

                    # Find the job location
                    location = job_detail.find_element(By.CSS_SELECTOR, 'div[data-test="location"]').text
                    print('Location Done')

                    # Job title is in the first h1 element
                    job_title = job_detail.find_element(By.CSS_SELECTOR, 'h1[aria-hidden="false"]').text
                    print('Job Title Done')

                    # Because the description have <p> and <ul>. Fetch all raw content atm
                    job_description = job_detail.find_element(By.XPATH, 'section/div[2]/div[1]').text
                    print('Job Description Done')

                    # Get job relative url to recheck data easily
                    job_url = job_card.find_element(By.CSS_SELECTOR, 'a[data-test="job-link"]').get_attribute('href')
                    print('URL Done')
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
                print("Job URL: {}".format(job_url))

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

            '''
            jobs.append({
                "Job ID": job_id,
                "Job Title": job_title,
                "Job Description": job_description,
                "Company ID": company_id,
                "Company Name": company_name,
                "Job URL": job_url,
                "Location": location,
                "Size": company_size,
                "Founded": company_founded,
                "Sector": company_sector,
            })
            '''
            # add job to data pipeline. Makesure you call it
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
            })
            # Added successfully collected job to collected job id lists
            collected_job_ids.add(job_id)

        # Clicking on the "next page" button
        try:
            driver.find_element(By.CSS_SELECTOR, 'button[data-test="load-more"]').click()
            time.sleep(1) # Add a brief pause between page loads
        except NoSuchElementException:
            print("No More Page or Scraping terminated before reaching target number of jobs. Needed {}, got {}.".format(num_jobs,
                                                                                                         len(collected_job_ids)))
            break

    # quit the driver when we're done
    driver.quit()
    print("Scraping Completed. Close Driver....")
    # return pd.DataFrame(jobs)  # This line converts the dictionary object into a pandas DataFrame.
