import networkx as nx
from pymongo import *
from bson.objectid import ObjectId

# returns a tuple with 0 index representing how many listings the component encompasses
# and the 1 index is a list of the usernames of the sellers in that component
def findConnectedComponents(G):

    visitedNodes = []
    connectedComponents = []
    totalListings = 0

    for node in nx.nodes(G):

        totalListings += G.node[node]["numListings"]

        if node in visitedNodes:
            continue

        compNumListings = G.node[node]["numListings"]
        currentComponent = [node]
        stack = [node]
        visitedNodes.append(node)

        while len(stack) > 0:

            nextNode = stack.pop()

            for child in nx.neighbors(G, nextNode):
                if child not in visitedNodes:
                    compNumListings += G.node[child]["numListings"]
                    currentComponent.append(child)
                    stack.append(child)
                    visitedNodes.append(child)

        connectedComponents += [(compNumListings, currentComponent)]

    percentPerComponent = []
    for component in connectedComponents:
        percentComponent = (component[0] * 100.0 / totalListings, component[1])
        percentPerComponent.append(percentComponent)

    return sorted(percentPerComponent, key=lambda tup: tup[0])[::-1]


def findNonSingularComponents(G):

    conComp = findConnectedComponents(G)
    nonSingComp = []

    for comp in conComp:

        if len(comp[1]) <= 1:
            continue

        stringComp = []
        for user in comp[1]:
            stringComp += [str(user.encode('ascii', 'ignore'))]             # convert to ascii
        nonSingComp += [(comp[0], stringComp)]

    return nonSingComp

G = nx.Graph()

client = MongoClient()
collection = client.gbp.DataNoDuplicates

cursor = collection.find()

userDict = {}

for doc in cursor:

    if doc["Seller"] not in userDict:
        userDict[doc["Seller"]] = set()

    userDict[doc["Seller"]].add(str(doc["_id"]))

for seller in userDict:

    # if len(userDict[seller]) < 3:
    #     continue

    if not G.has_node(seller):
        G.add_node(seller)

    #G.node[seller]["listings"] = userDict[seller]
    G.node[seller]["numListings"] = len(userDict[seller])

    for listingID in userDict[seller]:
        cursor = collection.find({"_id": ObjectId(listingID)})
        for doc in cursor:
            for key in doc["Related Listings"]:
                if key == "Title" or key == "Description Text" or key == "Images":
                    for listing in doc["Related Listings"][key]:
                        cursor2 = collection.find({"_id": ObjectId(listing)})
                        for doc2 in cursor2:
                            if str(doc["_id"]) == str(doc2["_id"]):
                                continue
                            if doc2["Seller"] == seller:
                                continue
                            if not G.has_node(doc2["Seller"]):
                                continue
                            if not G.has_edge(seller, doc2["Seller"]):
                                G.add_edge(seller, doc2["Seller"])

print findConnectedComponents(G)

nx.write_gexf(G, "GBPSellerGraph2.gexf")
