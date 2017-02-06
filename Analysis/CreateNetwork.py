import networkx as nx
from pymongo import *

G = nx.Graph()

client = MongoClient()
collection = client.gbp.DataNoDuplicates

cursor = collection.find()

attributes = ["URL", "Seller", "Marketplace", "Title", "Price", "Number of Reviews", "Review Feedback",
              "Item Condition", "Quote", "Location"]

for doc in cursor:

    # add attributes
    s_id = str(doc["_id"])

    if not G.has_node(s_id):
        G.add_node(s_id)

    for key in doc.keys():
        if key in attributes:
            G.node[s_id][key] = doc[key]

cursor = collection.find()

count = 0

for doc in cursor:
    s_id = str(doc["_id"])
    for keyName in doc["Related Listings"]:
        #
        # if keyName == "Seller":
        #     continue

        for listing in doc["Related Listings"][keyName]:
            d_id = str(listing)
            if d_id == s_id:
                continue
            if not G.has_node(d_id):
                continue
            if not G.has_edge(s_id, d_id):
                G.add_edge(s_id, d_id)
            G.edge[s_id][d_id][keyName] = True

nodeRanking = nx.eigenvector_centrality(G)

cursor = collection.find()

for doc in cursor:
    s_id = str(doc["_id"])
    G.node[s_id]["centrality"] = nodeRanking[s_id]



nx.write_gexf(G, "GBPGraph3.gexf")