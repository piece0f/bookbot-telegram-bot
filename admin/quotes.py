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
    author = quote[2]
    with open("authors", "r", encoding='utf-8') as authors:
        authors_list = authors.read().splitlines()
    with open("authors", "a", encoding='utf-8') as authors:
        if author not in authors_list:
            authors.write(author+'\n')
    db.insert_one({"Quote": quote[0],
                   "Book": quote[1],
                   "Author": '_'.join(author.split()),
                   "URL": quote[3],
                   "Users": []
                   })

print("\nSuccess!")
