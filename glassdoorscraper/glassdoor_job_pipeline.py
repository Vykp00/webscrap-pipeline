# ******************************************************************************
#  Copyright (c) 2024. Vy Kauppinen (VyKp00)
# ******************************************************************************
# This pipeline save collected data to csv file

import os
import time
import csv
from glassdoor_data_items import JobCard
from dataclasses import fields, asdict


class GlassdoorJobPipeline:

    def __init__(self, csv_filename="", storage_queue_limit=5):
        self.ids_seen = set()
        self.storage_queue = []
        # Hold a queue before sending to csv
        self.storage_queue_limit = storage_queue_limit
        self.csv_filename = csv_filename
        # Check if the csv file is opened or closed
        self.csv_file_open = False

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

        with open(self.csv_filename, mode= 'a', newline= '', encoding= 'utf-8') as output_file:
            writer = csv.DictWriter(output_file, fieldnames=keys)

            if not file_exist:
                writer.writeheader()
            for job in jobs_to_save:
                writer.writerow(asdict(job))

        self.csv_file_open = False

        pass

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
