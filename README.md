# Webscraping Pipelines
This repo contains 2 data pipelines that gather and preprocess data from Glassdoor and StackOverFlow and save them to PostgreSQL

## 1. Instructions - Glassdoor
Install required dependencies 
````pycon
pip install -r requirements.txt
````
Add a `.env` file in `glassdoorscraper` directory with the following variables
````.dotenv
# Specify Postgres Pipeline
MY_POSTGRES_HOST = "POSTGRES_HOST"
MY_POSTGRES_USER = "POSTGRES_USER"
MY_POSTGRES_PASSWORD_WIN = "POSTGRES_PASSWORD"

# Fake User Agent API https://scrapeops.io/docs/intro/
MY_SCRAPEOPS_API_KEY = "YOUR API KEYS"
````

Next created a databases which is needed to saved to PostgreSQL (by default, `postgres_db_name="jobglassdoor"`)
The `init.py` will save collected data to `job_listings` table by default. Thus, make sure a table is created first.
````postgresql
CREATE TABLE job_listings (
    job_id BIGINT PRIMARY KEY,
    job_title VARCHAR(255),
    job_description TEXT,
    company_id VARCHAR(50),
    company_name VARCHAR(255),
    job_url VARCHAR(255),
    job_location VARCHAR(100),
    company_size VARCHAR(100),
    founded_year VARCHAR(4),
    company_sector VARCHAR(100),
    country VARCHAR(100)
);
````
Finally, run the script in `init.py`
````pycon
python init.py
````
