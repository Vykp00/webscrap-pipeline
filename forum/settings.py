# Scrapy settings for forum project
"""
Author: Vykp00
"""
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html
import os
import dotenv
dotenv.load_dotenv()

BOT_NAME = "forum"

SPIDER_MODULES = ["forum.spiders"]
NEWSPIDER_MODULE = "forum.spiders"

# Crawl responsibly by identifying yourself (and your website) on the user-agent
# USER_AGENT = "forum (+http://www.yourdomain.com)"

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Specify MongoDB Pipeline
MONGODB_URI = "mongodb+srv://vykp:jkiivRE8O2UHD3JR@qa-forum.dzen7ex.mongodb.net/?retryWrites=true&w=majority&appName=QA-Forum"
MONGODB_DATABASE = "qa-forum"  # Database name
MONGODB_COLLECTION = "questions"  # DB Collection name

# Specify Postgres Pipeline
POSTGRES_HOST = os.getenv("MY_POSTGRES_HOST")
POSTGRES_USER = os.getenv("MY_POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("MY_POSTGRES_PASSWORD")
POSTGRES_FORUM_DB = os.getenv("MY_POSTGRES_FORUM_DB")
POSTGRES_STACK_DB = os.getenv("MY_POSTGRES_STACK_DB")

# Configure maximum concurrent requests performed by Scrapy (default: 16)
CONCURRENT_REQUESTS = 16

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
DOWNLOAD_DELAY = 0.75
# The download delay setting will honor only one of:
CONCURRENT_REQUESTS_PER_DOMAIN = 16
# CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
# COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
# TELNETCONSOLE_ENABLED = False

# Override the default request headers:
# DEFAULT_REQUEST_HEADERS = {
#    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
#    "Accept-Language": "en",
# }

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
# SPIDER_MIDDLEWARES = {
#    "forum.middlewares.ForumSpiderMiddleware": 543,
# }

# For Fake User Agent and Browser Header
SCRAPEOPS_API_KEY = os.getenv("MY_SCRAPEOPS_API_KEY")
SCRAPEOPS_FAKE_USER_AGENT_ENDPOINT = 'https://headers.scrapeops.io/v1/user-agents'
SCRAPEOPS_FAKE_BROWSERS_ENDPOINT = 'https://headers.scrapeops.io/v1/browser-headers'
SCRAPEOPS_PROXY_ENABLED = True
SCRAPEOPS_PROXY_SETTINGS = {'country': 'fi'}
SCRAPEOPS_FAKE_USER_AGENT_ENABLED = True
SCRAPEOPS_FAKE_BROWSERS_HEADER_ENABLED = True
SCRAPEOPS_NUM_RESULTS = 5
SCRAPEOPS_PROXY_ENABLED = True

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
    "forum.middlewares.ForumDownloaderMiddleware": None,
    "forum.middlewares.FakeBrowserHeaderAgentMiddleware": 300,
}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
# EXTENSIONS = {
#    "scrapy.extensions.telnet.TelnetConsole": None,
# }

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    "forum.pipelines.DuplicatesPipeline": 400,
    "forum.pipelines.ForumPipeline": 600,
    "forum.pipelines.SaveToPostgresPipeline": None,
    "forum.pipelines.SaveStackToPostgresPipeline": 800
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
# AUTOTHROTTLE_ENABLED = True
# The initial download delay
# AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
# AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
# AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
# AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
# HTTPCACHE_ENABLED = True
# HTTPCACHE_EXPIRATION_SECS = 0
# HTTPCACHE_DIR = "httpcache"
# HTTPCACHE_IGNORE_HTTP_CODES = []
# HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"
