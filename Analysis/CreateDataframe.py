from pymongo import *
import pandas as pd

client = MongoClient()
collection = client.gbp.test

cursor = collection.find()

columns = ["URL", "Seller", "Marketplace", "Title", "Price", "Number of Reviews", "Review Feedback", "Item Condition", "Quote", "Location"]

df_ = pd.DataFrame(columns = columns)
df_ = df_.fillna(0)

for i, doc in enumerate(cursor):
    data = [doc["URL"], doc["Seller"], doc["Marketplace"], doc["Title"], doc["Price"], doc["Number of Reviews"],
            doc["Review Feedback"], doc["Item Condition"], doc["Quote"], doc["Location"]]

    df_.loc[i] = data

df_.to_csv('gbpdata.csv')