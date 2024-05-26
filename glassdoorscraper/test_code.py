import header_demo as gs
from glassdoor_job_pipeline import GlassdoorPostgresPipeline

list_of_urls = [
    # DONE: United States (800+)
    # 'https://www.glassdoor.com/Job/united-states-serverless-jobs-SRCH_IL.0,13_IN1_KO14,24.htm',
    # DONE : United Kingdom (339+)
    # 'https://www.glassdoor.com/Job/united-kingdom-serverless-jobs-SRCH_IL.0,14_IN2_KO15,25.htm',
    # DONE: United Arab Emirates (8+)
    # 'https://www.glassdoor.com/Job/united-arab-emirates-serverless-jobs-SRCH_IL.0,20_IN6_KO21,31.htm',
    # TODO: India (1204+)
    #'https://www.glassdoor.com/Job/india-serverless-jobs-SRCH_IL.0,5_IN115_KO6,16.htm?sortBy=date_desc',
    # In case India sites overload and button disappear
    'https://www.glassdoor.com/Job/india-serverless-jobs-SRCH_IL.0,5_IN115_KO6,16.htm',
    # DONE : Australia (107+)
    # 'https://www.glassdoor.com/Job/australia-serverless-jobs-SRCH_IL.0,9_IN16_KO10,20.htm',
    # DONE : Singapore (96 +)
    # 'https://www.glassdoor.com/Job/singapore-singapore-serverless-jobs-SRCH_IL.0,19_IC3235921_KO20,30.htm',
    # DONE: South Africa (24 +)
    # 'https://www.glassdoor.com/Job/south-africa-serverless-jobs-SRCH_IL.0,12_IN211_KO13,23.htm',

]
data_pipeline = GlassdoorPostgresPipeline(postgres_db_name="jobglassdoor")

for url in list_of_urls:
    # TODO: Remember to change the country name
    df = gs.get_jobs(url, False, 5, data_pipeline, 'India')
data_pipeline.close_pipeline()

