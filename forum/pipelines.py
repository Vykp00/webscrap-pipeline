# Define your item pipelines here
"""
Author: Vykp00
"""
import logging
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import re

import psycopg2
# from scrapy.exceptions import DropItem
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem

from forum.items import QuestionItem, ReplyItem
from forum.settings import POSTGRES_HOST, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_FORUM_DB
from forum.text_utils import normalize_corpus  # For text cleaning

# useful for handling different item types with a single interface

# create logger
logger = logging.getLogger('__name__')
level = logging.INFO
logger.setLevel(level)

# ----> console info messages require these lines <----
# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(level)

# add ch to logger
logger.addHandler(ch)


# This pipeline drop
class DuplicatesPipeline:
    def __init__(self):
        self.ids_seen = set()

    def preprocess_items(self, item, spider):
        adapter = ItemAdapter(item)
        # Drop item if the question's id has already been process
        if adapter['id'] in self.ids_seen:
            raise DropItem(f'Duplicate item found: {item!r}')
        else:
            self.ids_seen.add(adapter['id'])
            return item


# This preprocesses and cleans the pipeline
class ForumPipeline:

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        # Strip all whitespaces from string except for content
        field_names = ['url']
        for field_name in field_names:
            value = adapter.get(field_name)
            if value is not None:
                adapter[field_name] = value.strip()

        # Convert Category to Lowercase
        lowercase_keys = ['category']
        for lowercase_key in lowercase_keys:
            value = adapter.get(lowercase_key)
            if value is not None:
                adapter[lowercase_key] = value.lower()

        # Convert id to number
        integer_keys = ['id', 'question_id']
        for integer_key in integer_keys:
            id_string = adapter.get(integer_key)
            if id_string is not None:
                adapter[integer_key] = int(id_string)

        # Convert like_num string to number
        like_value = adapter.get('like_num')
        if like_value is not None:
            # Use re.search() to find the first occurrence of the pattern in the text
            match = re.search(r'(\d+)\s+Like(?:s)?', like_value)
            if match:
                # Extract the number from the match group
                number = int(match.group(1))
                adapter['like_num'] = number
            else:
                adapter['like_num'] = 0  # Return None if no match is found

        # Content ---> Remove HTML syntax, commas, and '\n', and convert to a single continuous text
        content_strings = adapter.get('content')
        cleaned_text = ' '.join(content_strings)  # Concatenate all the text and remove extra space
        # Remove any @mentioned account in text. Basically any words containing '@'
        cleaned_text = re.sub(r'\b@\w+\b', ' ', cleaned_text)
        cleaned_text = cleaned_text.strip().replace(',', '')  # Clean html and coma syntax first"
        cleaned_text = normalize_corpus(cleaned_text, text_lower_case=False)
        # Join all cleaned strings to a single continuous text
        adapter['content'] = cleaned_text

        return item


# This pipeline save the data to postgres table
class SaveToPostgresPipeline:
    def __init__(self):
        # Connection Details
        hostname = POSTGRES_HOST
        user = POSTGRES_USER
        password = POSTGRES_PASSWORD
        database = POSTGRES_FORUM_DB

        # Create/Connect to database
        self.connection = psycopg2.connect(host=hostname, user=user, password=password, database=database)

        # Create cursor to execute query
        self.cur = self.connection.cursor()

        # Create question tables if none exist
        self.cur.execute(
            """CREATE TABLE IF NOT EXISTS qa_question (
            id SERIAL PRIMARY KEY,
            title TEXT,
            url TEXT,
            tags TEXT[],
            post_date TIMESTAMP WITH TIME ZONE,
            scrap_date TIMESTAMP WITH TIME ZONE,
            category VARCHAR(255),
            content TEXT);
            
            CREATE TABLE IF NOT EXISTS qa_reply (
            id SERIAL PRIMARY KEY,
            question_id INTEGER REFERENCES qa_question(id),
            domain VARCHAR(255),
            like_num INTEGER,
            created_date TIMESTAMP WITH TIME ZONE,
            scrap_date TIMESTAMP WITH TIME ZONE,
            content TEXT);
        """)

    def process_item(self, item, spider):
        # If this is a question
        if isinstance(item, QuestionItem):
            # Check to see if the question's id is already in database
            self.cur.execute("""SELECT * FROM qa_question WHERE id = %s;""", (item['id'],))
            result = self.cur.fetchone()

            # If the id already exist, create log message
            if result:
                logger.warning("Item already exists in database and won't be saved: %s" % item['id'])
                raise DropItem("Question Item won't be saved")

            # If the id is new, log the DB
            else:
                # Execute insert of data into databases
                try:
                    # Insert question data
                    self.cur.execute("""
                    INSERT INTO qa_question (
                    id, title, url, tags, post_date, scrap_date, category, content) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s);""", (
                        item['id'],
                        item['title'],
                        item['url'],
                        item['tags'],
                        item['post_date'],
                        item['scrap_date'],
                        item['category'],
                        str(item['content'])
                    ))

                    self.connection.commit()
                    logger.info("Item saved to qa_question DB: %s" % item['id'])
                except Exception as e:
                    # Error handling
                    self.connection.rollback()  # Roll back on error
                    logger.warning("Item couldn't be saved: %s" % item['id'])

        # If this is a reply
        if isinstance(item, ReplyItem):
            # Check to see if the reply's id is already in database
            self.cur.execute("""SELECT * FROM qa_reply WHERE id = %s;""", (item['id'],))
            result = self.cur.fetchone()

            # Check to see if the reply question's id is already in database
            self.cur.execute("SELECT id FROM qa_question WHERE id = %s", (item['question_id'],))
            question_exists = self.cur.fetchone()

            # If the id already exist, create log message
            if result:
                logger.warning("Item already exists in database and won't be saved: %s" % item['id'])
                raise DropItem(f'Duplicate item found: {item!r}')

            # If the question doesn't exist yet, drop item
            elif not question_exists:
                logger.warning("Question Item for this Reply doesn't exist: %s" % item['id'])
                raise DropItem(f'Drop Reply: {item!r}')

            # If the id is new, log the DB
            else:
                # Try inserting to database
                try:
                    self.cur.execute("""
                    INSERT INTO qa_reply (
                    id, question_id, domain, like_num, created_date, scrap_date, content) VALUES (
                    %s, %s, %s, %s, %s, %s, %s);""", (
                        item['id'],
                        item['question_id'],
                        item['domain'],
                        item['like_num'],
                        item['created_date'],
                        item['scrap_date'],
                        str(item['content'])
                    ))

                    self.connection.commit()
                    logger.info("Item saved to qa_reply DB: %s" % item['id'])
                except Exception as e:
                    # Roll back on error
                    self.connection.rollback()
                    logger.warning("Item couldn't be saved: %s" % item['id'])
        return item

    # Close connection after spyder close
    def close_spider(self, spider):
        # Close cursor  & connection database
        self.cur.close()
        self.connection.close()


'''
class MongoDBPipeline(object):

    def __init__(self):
        client = pymongo.MongoClient(
            "mongodb+srv://vykp:jkiivRE8O2UHD3JR@qa-forum.dzen7ex.mongodb.net/?retryWrites=true&w=majority&appName=QA-Forum")
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
