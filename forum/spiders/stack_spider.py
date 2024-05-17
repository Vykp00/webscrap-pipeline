# Create Spider to extract data from StackOverFlow
"""
Author: Vykp00
"""
from datetime import datetime
import scrapy
from scrapy import Spider, Selector

from forum.items import ForumItem, QuestionItem, ReplyItem
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
    def start_requests(self):
        allowed_domains = ['stackoverflow.com']
        # We want to fetch 50 questions per page sorted by the newest questions
        start_urls = [
            'https://stackoverflow.com/questions/tagged/openfaas?tab=newest&pagesize=50', # OpenFaas
            'https://stackoverflow.com/questions/tagged/zappa?tab=newest&pagesize=50', # Zappa
            'https://stackoverflow.com/search?q=vendia+serverless+express', # Vendia Serverless Express
            'https://stackoverflow.com/questions/tagged/serverless-framework?tab=newest&pagesize=50', # Serverless Framework
            'https://stackoverflow.com/questions/tagged/apache%2bopenwhisk', # Apache OpenWhisk
            'https://stackoverflow.com/questions/tagged/kubeless', # kubeless
            'https://stackoverflow.com/questions/tagged/knative?tab=newest&pagesize=50' # Knative
            'https://stackoverflow.com/search?tab=Relevance&pagesize=50&q=Fission', # Fission
            'https://stackoverflow.com/questions/tagged/fn', # Fn
            'https://stackoverflow.com/questions/tagged/iron.io?tab=newest&pagesize=50', # Iron.io
            'https://stackoverflow.com/questions/tagged/nuclio', # Nuclio

        ]
        for url in start_urls:
            yield scrapy.Request(url= get_proxy_url(url), callback=self.parse)

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
            try:
                next_page_rel = pagination[-1].attrib['rel']
                if next_page_rel == 'next':
                    next_page = pagination[-1].attrib['href']
                    next_page_url = 'https://stackoverflow.com' + next_page

                    # Then we trigger parse function again to fetch all question url from the new page
                    yield response.follow(next_page_url, callback=self.parse)
            except IndexError:
                pass


    # Here we fetch question content
    def parse_question_page(self, response):

        # ----- QUESTION ITEM -----
        # This contains question content and tags
        question_content = Selector(response).css('div#question')[0]

        # A tag list for all tag
        question_tag = []
        tag_div = question_content.css('ul.js-post-tag-list-wrapper')[0]
        if tag_div is not None:
            # Get each tag in <li>
            tag_list = tag_div.css('a.post-tag ::text').extract()
            question_tag = tag_list

        forum_question_items = ForumItem()
        forum_question_items['id'] = question_content.attrib['data-questionid']
        forum_question_items['title'] = Selector(response).css('a.question-hyperlink:nth-child(1) ::text').get()
        forum_question_items['url'] = response.url
        forum_question_items['tags'] = question_tag
        # Get question's created time. Timestamp follow ISO 8601 format
        forum_question_items['post_date'] = Selector(response).css('div.ws-nowrap:nth-child(1) > time:nth-child(2)').attrib['datetime']
        # Get Post scrap date
        forum_question_items['scrap_date'] = datetime.now().isoformat()
        # Question Raw Text
        forum_question_items['content'] = question_content.css('p ::text').extract()

        # Print yield question
        print("New Question added")
        yield forum_question_items

        # ----- Stack Overflow Answer Item (ReplyItem) ----
        is_answer = False
        answers = Selector(response).css('div.answer')
        # If there is an answer
        try:
            # Check if there's at least one answer
            answer_1 = answers[0]
            is_answer = True
            print("Answer Exist")
            for answer in answers:
                answer_item = ReplyItem()
                answer_item['id'] = answer.attrib['data-answerid']
                answer_item['question_id'] = answer.attrib['data-parentid']
                answer_item['domain'] = 'stackoverflow.com'
                answer_item['like_num'] = answer.attrib['data-score'] + ' Likes'
                answer_item['created_date'] = answer.css('span.relativetime').attrib['title']
                # Get the current scrap date and time in ISO 8601 format
                answer_item['scrap_date'] = datetime.now().isoformat()
                answer_item['content'] = answer.css('div.s-prose p ::text').extract()

                yield answer_item
        except IndexError:
            # If there's no answers, yield forum question only
            print('No Answer in question: ', forum_question_items['id'])
