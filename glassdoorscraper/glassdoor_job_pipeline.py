# ******************************************************************************
#  Copyright (c) 2024. Vy Kauppinen (VyKp00)
# ******************************************************************************
# This pipeline save collected data to csv file
import psycopg2
import os
import time
import csv
from glassdoor_data_items import JobCard
from dataclasses import fields, asdict

# For virtual environment
import dotenv

dotenv.load_dotenv('.env')

# Specify Postgres Pipeline
POSTGRES_HOST = os.getenv("MY_POSTGRES_HOST")
POSTGRES_USER = os.getenv("MY_POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("MY_POSTGRES_PASSWORD_WIN")
POSTGRES_JOB_DB = os.getenv("MY_POSTGRES_GLASSDOOR_DB")

# ******** CREATE A LOGGER ********
import logging


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
logger = logging.getLogger('__pipeline__')
level = logging.WARNING
logger.setLevel(level)

# Create console handler
# c_handler = logging.StreamHandler()
# c_handler.setLevel(level)
# #
# # # Create formatter
# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# #
# # # Add formatter to ch
# c_handler.setFormatter(formatter)
# #
# # # Add ch to logger
# logger.addHandler(c_handler)


# This pipelines save the data to csv files
class GlassdoorJobPipeline:

    def __init__(self, csv_filename="", storage_queue_limit=5):
        self.ids_seen = set()
        self.storage_queue = []
        # Hold a queue before sending to csv
        self.storage_queue_limit = storage_queue_limit
        self.csv_filename = csv_filename
        # Check if the csv file is opened or closed
        self.csv_file_open = False

        # Connect to Postgres Data
        self.connection = psycopg2.connect(
            host=POSTGRES_HOST,
            databases=self.postgre_db_name,
            user=POSTGRES_USER,
            password=POSTGRES_JOB_DB
        )

    # Periodically save the jobs stored in the pipeline to the csv files
    # The number of job is determined by storage_queue_limit
    # The code add new columns to csv file if it exists
    def save_to_csv(self):
        self.csv_file_open = True
        jobs_to_save = []
        jobs_to_save.extend(self.storage_queue)
        self.storage_queue.clear()
        if not jobs_to_save:
            return
        keys = [field.name for field in fields(jobs_to_save[0])]
        file_exist = (
                os.path.isfile(self.csv_filename) and os.path.getsize(self.csv_filename) > 0
        )

        with open(self.csv_filename, mode='a', newline='', encoding='utf-8') as output_file:
            writer = csv.DictWriter(output_file, fieldnames=keys)

            if not file_exist:
                writer.writeheader()
            for job in jobs_to_save:
                writer.writerow(asdict(job))

        self.csv_file_open = False

    def clean_raw_job(self, raw_data):
        return JobCard(
            job_id_string=raw_data.get('job_id', ""),
            job_title=raw_data.get('job_title', ""),
            job_description=raw_data.get('job_description', ""),
            company_id=raw_data.get('company_id', ""),
            company_name=raw_data.get('company_name', ""),
            job_url=raw_data.get('job_url', ""),
            job_location=raw_data.get('location', ""),
            company_size=raw_data.get('company_size', ""),
            founded_year=raw_data.get('company_founded', ""),
            company_sector=raw_data.get('company_sector', ""),
        )

    # Check if a job is a duplicate based on the job's id.
    # This only check that it has been encountered in the pipeline
    def is_duplicate(self, job_data):
        if job_data.job_id in self.ids_seen:
            print(f'Duplicate job found: {job_data.job_id}. Item dropped.')
            return True
        self.ids_seen.add(job_data.job_id)
        return False

    # Finally, add the job to the pipeline after cleaning and duplicate proof
    def add_job(self, raw_data):
        job = self.clean_raw_job(raw_data)
        # If the job is not duplicate
        if self.is_duplicate(job) == False:
            self.storage_queue.append(job)
            if (
                    len(self.storage_queue) >= self.storage_queue_limit
                    and self.csv_file_open == False
            ):
                self.save_to_csv()

    def close_pipeline(self):
        if self.csv_file_open:
            time.sleep(3)
        if len(self.storage_queue) > 0:
            self.save_to_csv()


# This pipeline save the data to PostgresSQL
class GlassdoorPostgresPipeline:
    def __init__(self, postgres_db_name="", storage_queue_limit=5):
        self.ids_seen = set()
        self.storage_queue = []
        # Hold a queue before sending to csv
        self.storage_queue_limit = storage_queue_limit
        self.postgres_db_name = postgres_db_name
        # Check if the csv file is opened or closed
        self.data_stored = False  # Flag to track if data is stored

        # Connect to Postgres Data
        self.connection = psycopg2.connect(
            host=POSTGRES_HOST,
            database=self.postgres_db_name,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD
        )

        # Create cursor to execute query
        self.cursor = self.connection.cursor()

    # Periodically save the jobs stored in the pipeline to Postgres
    # The number of job is determined by storage_queue_limit
    # The code add new columns to csv file if it exists
    def save_to_postgres(self):
        jobs_to_save = []
        jobs_to_save.extend(self.storage_queue)

        # Clear the old data which is saved already
        self.storage_queue.clear()

        if not jobs_to_save:
            return

        for job in jobs_to_save:
            item = asdict(job)
            # Execute insert of data into job_listings. Assumed you have that table in the database
            self.cursor.execute("""SELECT * FROM job_listings WHERE job_id =%s;""", (item['job_id'],))
            search_result = self.cursor.fetchone()

            if search_result:
                logger.warning("Item already exists in database and won't be saved: %s" % item['job_id'])
                continue
            else:
                # If the id is new, log the DB
                try:
                    self.cursor.execute("""INSERT INTO job_listings (
                    job_id, job_title, job_description, company_id, company_name, job_url, job_location, company_size, founded_year, company_sector, country) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);""",
                                        (item['job_id'], item['job_title'], str(item['job_description']),
                                         item['company_id'], item['company_name'],
                                         item['job_url'], item['job_location'], item['company_size'],
                                         item['founded_year'], item['company_sector'], item['country']),
                                        )
                    self.connection.commit()
                    logger.info("-------New Item saved to job_listings: %s" % item['job_id'])
                except Exception as e:
                    # Error handling
                    self.connection.rollback()  # Roll back on error
                    logger.warning("********Item couldn't be saved: %s" % item['job_id'])
                    logger.exception(e)

    def clean_raw_job(self, raw_data):
        return JobCard(
            job_id_string=raw_data.get('job_id', ""),
            job_title=raw_data.get('job_title', ""),
            job_description=raw_data.get('job_description', ""),
            company_id=raw_data.get('company_id', ""),
            company_name=raw_data.get('company_name', ""),
            job_url=raw_data.get('job_url', ""),
            job_location=raw_data.get('job_location', ""),
            company_size=raw_data.get('company_size', ""),
            founded_year=raw_data.get('founded_year', ""),
            company_sector=raw_data.get('company_sector', ""),
            country=raw_data.get('country', ""),
        )

    # Check if a job is a duplicate based on the job's id.
    '''
    if job_data.job_id in self.ids_seen:
        print(f'Duplicate job found: {job_data.job_id}. Item dropped.')
        return True
    self.ids_seen.add(job_data.job_id)
    '''

    def is_duplicate(self, job_data):
        # First we check if that data item is already in pipeline
        if job_data.job_id in self.ids_seen:
            print(f'Duplicate job found: {job_data.job_id}. Item dropped.')
            return True
        self.ids_seen.add(job_data.job_id)
        return False

    # Finally, add the job to the pipeline after cleaning and duplicate proof
    def add_job(self, raw_data):
        job = self.clean_raw_job(raw_data)
        # If the job is not duplicate
        if not self.is_duplicate(job):
            self.storage_queue.append(job)
            if len(self.storage_queue) >= self.storage_queue_limit:
                self.save_to_postgres()
                self.data_stored = True  # Set Flag to True when data is stored

    def close_pipeline(self):
        if len(self.storage_queue) > 0:
            self.save_to_postgres()
            if self.data_stored:  # Check if data is stored before printing
                print('Data pipeline closed. Saved data to {} databases.'.format(self.postgres_db_name))
            else:
                print('No data to save. Closing Postgres Pipelines')
        else:
            print('No data to save. Closing Postgres Pipeline.')
