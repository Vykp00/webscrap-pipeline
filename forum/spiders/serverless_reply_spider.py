# This is the spider file to scrap reply from Serverless Forum
"""
Author: Vykp00
"""
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

    # We can check each questions if it has any reply
    def parse(self, response):
        # Grab all table data with the questions content
        question_rows = response.xpath('//tr[@class="topic-list-item"]')
        # Ignore the header post
        ignored_ids = ["18", "19", "2541"]

        for question_row in question_rows:
            # Get question id
            question_link = question_row.css('td > span > a').attrib['href']
            question_id = question_link.split('/')[-1]

            # Check if question_id is in the ignore list. If not, scrap the reply
            if question_id not in ignored_ids:
                # Check if it has reply
                reply_number = int(question_row.xpath('td[@class="replies"]/span//text()').get())

                if reply_number > 0:
                    # This trigger the parse_reply_page callback to extract individual reply.
                    yield scrapy.Request(question_link, callback=self.parse_reply_page)

        # Next page
        next_page = response.xpath('/html/body/div[1]/div[2]/span/b/a/@href').get()
        # Iterate through all pages until it reach the bottom
        if next_page is not None:
            next_page_url = 'https://forum.serverless.com' + next_page

            # Then we trigger parse function again to fetch all question url from the new page
            yield response.follow(next_page_url, callback=self.parse)

    # Fetch each reply
    def parse_reply_page(self, response):
        # This contains whole reply containers
        replies = response.xpath('//div[@itemprop="comment"]')
        # Fetch question id
        question_id = response.url.split('/')[-1]

        for reply in replies:
            # Get each reply position. The reply always starts from '2'
            reply_position = reply.css('div > span.crawler-post-infos > span ::text').extract()[0]
            reply_item = ReplyItem()
            # The comment don't have any id exposed on HTML. So we created our own
            reply_item['id'] = question_id + reply_position
            reply_item['question_id'] = question_id
            reply_item['domain'] = 'forum.serverless.com'
            try:
                reply_item['like_num'] = reply.xpath('div[3]/span[@class="post-likes"]//text()').extract()[0]
            except IndexError:
                # Incase there's no like
                reply_item['like_num'] = '0 Like'
            # Get reply post time
            reply_item['created_date'] = reply.css('div > span.crawler-post-infos > time.post-time').attrib['datetime']
            # Get the current scrap date and time in ISO 8601 format
            reply_item['scrap_date'] = datetime.now().isoformat()
            reply_item['content'] = reply.css('div.post p ::text').extract()  # This includes all text and @mention

            yield reply_item
