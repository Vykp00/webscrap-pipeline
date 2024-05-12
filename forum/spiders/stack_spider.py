# Create Spider to extract data from StackOverFlow
"""
Author: Vykp00
"""
import scrapy
from scrapy import Spider, Selector

from forum.items import ForumItem
from urllib.parse import urlencode
from forum.settings import SCRAPEOPS_API_KEY

# Set up Rotating Proxy for StackOverFlow
"""
OpenFaas, Zappa, Up, Vendia Serverless Express, Serverless Framework, Apache OpenWhisk, kubeless, Knative, Fission, Fn, Iron.io,  Nuclio
"""

def get_proxy_url(url):
    payload = {'api_key': SCRAPEOPS_API_KEY, 'url': url}
    proxy_url = 'https://proxy.scrapeops.io/v1/?' + urlencode(payload)
    return proxy_url
class StackSpider(Spider):
    name = 'stack'
    allowed_domains = ['stackoverflow.com']
    # We want to fetch 50 questions per page sorted by the newest questions
    start_urls = [
        'https://stackoverflow.com/questions/tagged/openfaas?tab=newest&pagesize=50', # OpenFaas
        'https://stackoverflow.com/questions/tagged/zappa?tab=newest&pagesize=50', # Zappa
        #'https://stackoverflow.com/search?q=vendia+serverless+express', # Vendia Serverless Express
        #'https://stackoverflow.com/questions/tagged/serverless-framework?tab=newest&pagesize=50', # Serverless Framework
    ]

    # We need to create full question URL to extract all data from the question
    def parse(self, response):
        # Grab all h3 element of div with class s-post-summary--content
        questions = Selector(response).css('div.s-post-summary')

        # Extract relative url of the question
        for question in questions:
            relative_url = question.css('a.s-link').attrib['href']
            full_url = 'https://stackoverflow.com' + relative_url

            # Call parse_question_page to yield the question
            yield scrapy.Request(full_url, callback=self.parse_question_page)

        # Go to next page
        # Because next page has the same class name with other page.
        pagination = Selector(response).css('a.js-pagination-item')
        if pagination is not None:
            # Fetch the last one <a> attribute from the pagination
            # Verify it's the 'Next' page. It should return 'next'. If not ''
            next_page_rel = pagination[-1].attrib['rel']
            if next_page_rel == 'next':
                next_page = pagination[-1].attrib['href']
                next_page_url = 'https://stackoverflow.com' + next_page

                # Then we trigger parse function again to fetch all question url from the new page
                yield response.follow(next_page_url, callback=self.parse)


    # Here we fetch question content
    def parse_question_page(self, response):
        # This contains question's title

        return None

