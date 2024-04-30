# Create Spider to extract data from Serverless Framework Forum
"""
NOTE: Unlike StackOverflow, Serverless as built with Discourse whose class tags and css tags are added
with Javascript. So what you see on browsers are different than what you can fetch with BeautifulSoup or Scrapy.
To accurately mine the data, here what you need to do:
    1. run $scrapy shell
    2. run $fetch('https://forum.serverless.com/c/serverless-framework/5')
    3. run view(response)
For step 3, it open the given response in your local web browser, for inspection.
However, that this will create a temporary file in your computer, which won’t be removed automatically.
    4. start fetch the tags from here
"""

from datetime import datetime

import scrapy
from scrapy import Spider
from forum.items import ForumItem, QuestionItem


class ServerlessSpider(Spider):
    name = 'serverless'  # This is the name you call on scrapy shell
    allowed_domains = ['forum.serverless.com']
    # We need to fetch all questions from all three categories
    start_urls = [
        'https://forum.serverless.com/c/serverless-framework/5',
        'https://forum.serverless.com/c/serverless-architectures/6',
        'https://forum.serverless.com/c/event-gateway/8',
    ]

    # We need to create full question URL to extract all data from the question
    # Get the all post results '//td[@class="main-link"]'
    def parse(self, response):
        # Grab all table data with the questions content
        posts = response.xpath('//td[@class="main-link"]')
        # Ignore the header post
        ignored_ids = ["18", "19", "2541"]

        # We will iterate through each post url via its relative link
        # //a[@class="title raw-link raw-topic-link"]//text()

        for post in posts:
            relative_url = post.xpath('span/a').attrib['href']
            post_id = relative_url.split('/')[-1]

            # Check if post id is in the ignored id. If not, we will yield and scrap the data
            # If not, it skips
            if post_id not in ignored_ids:
                # This trigger the parse_book_page callback to extract individual question's post.
                yield scrapy.Request(relative_url, callback=self.parse_post_page)

            '''
            tags = []
            bottom_line = post.xpath('div/div')
            if bottom_line is not None:
                for element in bottom_line.xpath('a[@class="discourse-tag"]//text()'):
                    tags.append(element.get())
            yield {
                'title': post.xpath('span/a//text()').get(),
                'url': post.xpath('span/a').attrib['href'],
                'tags': tags
            }
            '''

            # Go to Next page it give us the relative path such as /c/serverless-framework/5?page=1
            next_page = response.xpath('/html/body/div[1]/div[2]/span/b/a/@href').get()
            # Iterate through all pages until it reach the bottom
            if next_page is not None:
                next_page_url = 'https://forum.serverless.com' + next_page

                # Then we trigger parse function again to fetch all question url from the new page
                yield response.follow(next_page_url, callback=self.parse)

    # Here we fetch each post content
    def parse_post_page(self, response):
        # This contains question's title, category, and tags
        headlines = response.css('div#topic-title')[0]
        # This post content contains created date and question content
        post_contents = response.xpath('//*[@id="post_1"]')[0]

        # Create a list to collect all tags
        tags = []
        tag_div = headlines.css('div.discourse-tags:nth-child(1)')
        if tag_div is not None:
            # Get all each tag in div and append to new list
            for tag in tag_div.xpath('a[@class="discourse-tag"]//text()'):
                tags.append(tag.get())

        question_items = QuestionItem()
        question_items['id'] = response.url.split('/')[-1]  # Fetch question id
        question_items['title'] = headlines.xpath('h1/a//text()').get()  # Fetch title
        question_items['url'] = response.url
        question_items['tags'] = tags
        # Get question's created time
        question_items['post_date'] = post_contents.css('time.post-time').attrib['datetime']
        # Get the current scrap date and time in ISO 8601 format
        question_items['scrap_date'] = datetime.now().isoformat()
        # Fetch category
        question_items['category'] = headlines.xpath('//span[@class="category-name"]//text()').get()
        question_items['content'] = post_contents.css('p ::text').extract()  # This includes all text from html syntax
        # and html tags, we should clean it again
        yield question_items
