import header_demo as gs
import pandas as pd

url = 'https://www.glassdoor.com/Job/united-states-microservice-jobs-SRCH_IL.0,13_IN1_KO14,26.htm?sortBy=date_desc&jobTypeIndeed=CF3CP'

df = gs.get_jobs(url, 10, True, 3)

df.to_csv('glassdoor_jobs_raw_10.csv', index = False)
