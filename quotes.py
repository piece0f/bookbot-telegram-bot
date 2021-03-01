# -*- coding: utf-8 -*-

# small set of quotes for test

import pymongo
import os

mongoDB = os.environ.get('mongoDB')
client = pymongo.MongoClient(f"{mongoDB}")
db = client["BookBot"]["quotes_queue"]

with open('quotes_4_add.txt', 'r', encoding='utf-8') as f:
    quotes_raw = f.read().splitlines()
quotes = []
for quote in quotes_raw:
    quotes.append(quote.split('%'))


for quote in quotes:
    print(quote)
    db.insert_one({"Quote": quote[0],
                   "Book": quote[1],
                   "Author": '_'.join(quote[2].split()),
                   "URL": quote[3],
                   "Users": []
                   })

print("\nSuccess!")
