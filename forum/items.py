# Define here the models for your scraped items
"""
Author: Vykp00
"""
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class ForumItem(scrapy.Item):
    # define the fields for your item here like:
    id = scrapy.Field()
    title = scrapy.Field()  # Question Title
    url = scrapy.Field()  # Question URL
    tags = scrapy.Field()  # Questions tags
    post_date = scrapy.Field()  # Question's posted date
    scrap_date = scrapy.Field()  # The date this question was scraped
    content = scrapy.Field()  # Question content


# inherit class from Forum for Serverless Forum
class QuestionItem(ForumItem):
    category = scrapy.Field()  # Question category


# This item is for scraping reply from Forum
class ReplyItem(scrapy.Item):
    id = scrapy.Field()
    question_id = scrapy.Field()  # Question's id  for reference with SQL
    domain = scrapy.Field()  # Domain origin of the reply
    like_num = scrapy.Field()  # Number of likes of the reply
    created_date = scrapy.Field()  # Reply's created date
    scrap_date = scrapy.Field()  # The date this reply was scraped
    content = scrapy.Field()  # Reply content

#class AnswerItem(scrapy.Item):