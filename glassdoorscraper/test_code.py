import header_demo as gs
import pandas as pd

url = 'https://www.glassdoor.com/Job/united-states-microservice-jobs-SRCH_IL.0,13_IN1_KO14,26.htm?sortBy=date_desc&jobTypeIndeed=CF3CP'
url2 = 'https://www.glassdoor.com/Job/india-microservice-jobs-SRCH_IL.0,5_IN115_KO6,18.htm?sortBy=date_desc&jobTypeIndeed=CF3CP'
df = gs.get_jobs(url2, 45, True, 3)

df.to_csv('../databases/samples/glassdoor_jobs_raw_30.csv', index = False)
