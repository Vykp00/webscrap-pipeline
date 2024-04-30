# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import psycopg2
# useful for handling different item types with a single interface

# from scrapy.exceptions import DropItem
from itemadapter import ItemAdapter
from forum.text_utils import normalize_corpus  # For text cleaning
from scrapy.exceptions import DropItem
from forum.settings import POSTGRES_HOST, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB


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
            adapter[field_name] = value.strip()

        # Convert Category to Lowercase
        lowercase_keys = ['category']
        for lowercase_key in lowercase_keys:
            value = adapter.get(lowercase_key)
            adapter[lowercase_key] = value.lower()

        # Convert id to number
        id_string = adapter.get('id')
        adapter['id'] = int(id_string)

        # Content ---> Remove HTML syntax, commas, and '\n', and convert to a single continuous text
        content_strings = adapter.get('content')
        cleaned_text = ' '.join(content_strings)  # Concatenate all the text and remove extra space
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
        database = POSTGRES_DB

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
            content TEXT)
        """)

    def process_item(self, item, spider):

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
        except Exception as e:
            # Error handling
            self.connection.rollback()  # Roll back on error
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
