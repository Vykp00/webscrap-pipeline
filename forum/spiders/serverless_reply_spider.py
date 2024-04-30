# This is the spider file to scrap reply from Serverless Forum
from datetime import datetime

import scrapy
from scrapy import Spider
from forum.items import ReplyItem

class ServerlessReplySpider(Spider):
    name = 'serverless_reply'  # Spider name call
    allowed_domains = ['forum.serverless.com']
    # We need to fetch all questions from all three categories
    start_urls = [
        'https://forum.serverless.com/c/serverless-framework/5',
        'https://forum.serverless.com/c/serverless-architectures/6',
        'https://forum.serverless.com/c/event-gateway/8',
    ]

    # We can create