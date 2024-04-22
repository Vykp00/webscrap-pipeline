# Create Spider to extract data from StackOverFlow

from scrapy import Spider, Selector
from forum.items import ForumItem


class StackSpider(Spider):
    name = 'stack'
    allowed_domains = ['stackoverflow.com']
    # We want to fetch 50 questions per page sorted by the newest questions
    start_urls = [
        'https://stackoverflow.com/questions?tab=newest&pagesize=50',
    ]

    # We need to create full question URL to extract all data from the question
    def parse(self, response):
        # Grab all h3 element of div with class s-post-summary--content
        questions = Selector(response).xpath('//div[@class="s-post-summary--content"]/h3')

        # Extract relative url of the question
        for question in questions:
            item = ForumItem()
            item['title'] = question.xpath('a[@class="s-link"]/text()').extract()[0]
            item['url'] = question.xpath('a[@class="s-link"]/@href').extract()[0]
            yield item
