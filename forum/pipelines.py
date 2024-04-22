# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import pymongo

from scrapy.exceptions import DropItem
from scrapy import log

'''
from pymongo.mongo_client import MongoClient
uri = "mongodb+srv://vykp:jkiivRE8O2UHD3JR@qa-forum.dzen7ex.mongodb.net/?retryWrites=true&w=majority&appName=QA-Forum"
# Create a new client and connect to the server
client = MongoClient(uri)
# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)
'''


class MongoDBPipeline(object):

    def __init__(self):
        client = pymongo.MongoClient("mongodb+srv://vykp:jkiivRE8O2UHD3JR@qa-forum.dzen7ex.mongodb.net/?retryWrites=true&w=majority&appName=QA-Forum")
        db = client["qa-forum"]
        self.collection = db["questions"]
        # Send a ping to confirm a successful connection
        try:
            client.admin.command('ping')
            print("Pinged your deployment. You successfully connected to MongoDB!")
        except Exception as e:
            print(e)

    # This process the parsed data by establishing a connection to the database
    # unpack the data, and then save it to the database
    def process_item(self, item, spider):
        valid = True
        for data in item:
            if not data:
                valid = False
                raise DropItem("Missing {0}!".format(data))
        if valid:
            self.collection.insert(dict(item))
            log.msq("Question added to MongoDB",
                    level=log.DEBUG, spider=spider)

        return item

'''
class ForumPipeline:
    def process_item(self, item, spider):
        return item
'''