from pymongo import *
import nltk
import string
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from PIL import Image
import urllib, cStringIO
import distance
import httplib2
from bson.objectid import ObjectId


def reset(coll):

    print "Resetting Related Listings..."

    cursor = coll.find()
    for doc in cursor:
        coll.update({"URL": doc["URL"]}, {'$set': {"Related Listings": {}}})

    print "Finished Related Listings Reset"


def relateSellers(coll):

    print "Starting Seller Analysis..."

    cursor = coll.find()

    for doc in cursor:

        if "Seller" not in doc:
            continue

        cursor2 = coll.find({"Seller":  doc["Seller"]})

        for match in cursor2:

            if doc["URL"] == match["URL"]:
                continue

            if "Seller" not in match["Related Listings"]:
                match["Related Listings"]["Seller"] = set()

            # MongoDB can't store sets
            match["Related Listings"]["Seller"] = set(match["Related Listings"]["Seller"])
            match["Related Listings"]["Seller"].add(str(doc["_id"]))
            match["Related Listings"]["Seller"] = list(match["Related Listings"]["Seller"])

            coll.update({"URL" : match["URL"]}, {'$set': {"Related Listings.Seller" : match["Related Listings"]["Seller"]}})

    print "Finished Seller Analysis"


def get_tokens(text):

    text = str(text).lower()
    no_punctuation = text.translate(None, string.punctuation)
    tokens = nltk.word_tokenize(no_punctuation)

    filtered = []

    for token in tokens:
        if token not in stopwords.words('english'):
            filtered.append(token)

    return filtered


def relateTitles(coll):

    print "Starting Title Analysis..."

    cursor = coll.find()
    titleList = []

    print "Getting Titles..."

    for doc in cursor:
        titleList.append(doc["Title"])

    print "Calculating TF-IDF..."

    # calculate the tf-idf matrix
    tfidf = TfidfVectorizer(tokenizer=get_tokens, stop_words='english')
    tfs = tfidf.fit_transform(titleList)
    tfsArray = (tfs * tfs.T).A

    print "Inserting into Mongo..."

    cursor = coll.find()

    for i, doc in enumerate(cursor):

        cursor2 = coll.find()

        for j, doc2 in enumerate(cursor2):

            if "Title" in doc and "Title" in doc2:
                closeness = tfsArray[i][j]

                if closeness > .8:

                    if "Title" not in doc2["Related Listings"]:
                        doc2["Related Listings"]["Title"] = set()

                    # MongoDB can't store sets
                    doc2["Related Listings"]["Title"] = set(doc2["Related Listings"]["Title"])
                    doc2["Related Listings"]["Title"].add(str(doc["_id"]))
                    doc2["Related Listings"]["Title"] = list(doc2["Related Listings"]["Title"])

                    coll.update({"URL" : doc2["URL"]}, {'$set': {"Related Listings.Title" : doc2["Related Listings"]["Title"]}})

            else:
                continue

    print "Finished Title Analysis"


def relateText(coll):

    print "Starting Text Analysis..."

    cursor = coll.find()
    textList = []

    print "Getting Text..."

    for doc in cursor:
        textList.append(doc["Description Text"])

    print "Calculating TF-IDF..."

    # calculate the tf-idf matrix
    tfidf = TfidfVectorizer(tokenizer=get_tokens, stop_words='english')
    tfs = tfidf.fit_transform(textList)
    tfsArray = (tfs * tfs.T).A

    print "Inserting into Mongo..."

    cursor = coll.find()

    for i, doc in enumerate(cursor):

        cursor2 = coll.find()

        for j, doc2 in enumerate(cursor2):

            if "Description Text" in doc and "Description Text" in doc2:
                closeness = tfsArray[i][j]

                if closeness > .8:
                    if "Description Text" not in doc2["Related Listings"]:
                        doc2["Related Listings"]["Description Text"] = set()

                    # MongoDB can't store sets
                    doc2["Related Listings"]["Description Text"] = set(doc2["Related Listings"]["Description Text"])
                    doc2["Related Listings"]["Description Text"].add(str(doc["_id"]))
                    doc2["Related Listings"]["Description Text"] = list(doc2["Related Listings"]["Description Text"])

                    coll.update({"URL" : doc2["URL"]}, {'$set': {"Related Listings.Description Text" : doc2["Related Listings"]["Description Text"]}})

            else:
                continue

    print "Finished Text Analysis"


# http://blog.iconfinder.com/detecting-duplicate-images-using-python/
def dHashImage(url):

    try:
        h = httplib2.Http()
        resp = h.request(url, 'HEAD')

    except:
        return -1

    # http://stackoverflow.com/questions/7391945/how-do-i-read-image-data-from-a-url-in-python
    try:
        file = cStringIO.StringIO(urllib.urlopen(url).read())
        img = Image.open(file)

    except:
        return -1

    img = img.convert('L').resize(
            (9, 8),
            Image.ANTIALIAS
    )

    width, height = img.size
    difference = []

    for row in xrange(height):
        for col in xrange(width-1):

            pixel_left = img.getpixel((col, row))
            pixel_right = img.getpixel((col+1, row))
            difference.append(pixel_left > pixel_right)

    decimal_value = 0
    hex_string = []

    for index, value in enumerate(difference):

        if value:
            decimal_value += 2**(index%8)

        if (index%8) == 7:
            hex_string.append(hex(decimal_value)[2:].rjust(2, '0'))
            decimal_value = 0

    return ''.join(hex_string)


def hashListingImages(coll):

    print "Calculating Hashes..."

    cursor = coll.find().batch_size(10)

    for doc in cursor:

        imageHashes = set()

        if "ImageURLs" in doc:
            for imageURL in doc["ImageURLs"]:
                imghash = dHashImage(imageURL)
                if imghash != -1:
                    imageHashes.add(imghash)

        if "Description Image URLs" in doc:
            for imageURL in doc["Description Image URLs"]:
                imghash = dHashImage(imageURL)
                if imghash != -1:
                    imageHashes.add(imghash)

        imageHashes = list(imageHashes)

        coll.update({"URL": doc["URL"]}, {'$set': {"imageHashes": imageHashes}})


def updateRelatedListingsImages(coll):

    cursor = coll.find().batch_size(10)

    for i, doc in enumerate(cursor):

        cursor2 = coll.find()

        for j, doc2 in enumerate(cursor2):

            related = False

            if "imageHashes" in doc and "imageHashes" in doc2:
                for hash1 in doc["imageHashes"]:
                    for hash2 in doc2["imageHashes"]:
                        if distance.levenshtein(hash1, hash2) <= 2:
                            related = True
                            break
                    if related:
                        break

            if related:

                if "Images" not in doc2["Related Listings"]:
                    doc2["Related Listings"]["Images"] = set()

                # MongoDB can't store sets
                doc2["Related Listings"]["Images"] = set(doc2["Related Listings"]["Images"])
                doc2["Related Listings"]["Images"].add(str(doc["_id"]))
                doc2["Related Listings"]["Images"] = list(doc2["Related Listings"]["Images"])

                coll.update({"URL": doc2["URL"]},
                            {'$set': {"Related Listings.Images" : doc2["Related Listings"]["Images"]}}
                            )


def removeDefaultImages(coll):

    # dHashImage("http://i.ebayimg.com/images/g/yGgAAOxyWmxSUwkf/s-l500.jpg")
    defaultHash = "01261f1303433902"

    cursor = coll.find()

    for doc in cursor:
        if "imageHashes" in doc:
            filteredHashes = doc["imageHashes"]
            for hash in doc["imageHashes"]:
                if distance.levenshtein(hash, defaultHash) <= 2:
                    filteredHashes.remove(hash)
            doc["imageHashes"] = filteredHashes

            coll.update({"URL": doc["URL"]},{'$set': {"imageHashes": doc["imageHashes"]}})


def relateImages(coll):

    print "Starting Image Analysis..."

    hashListingImages(coll)

    print "Cleaning Hashes..."

    removeDefaultImages(coll)

    print "Looking For Relationships..."

    updateRelatedListingsImages(coll)

    print "Finished Image Analysis"


def relateLocations(coll):

    print "Relating Listing Locations..."

    cursor = coll.find()

    locationToListing = {}

    for doc in cursor:
        if "Location" in doc:
            if doc["Location"] is not None and doc["Location"] is not "":
                if doc["Location"] not in locationToListing:
                    locationToListing[doc["Location"]] = []

                locationToListing[doc["Location"]] += [str(doc["_id"])]

    for location in locationToListing:
        for listing in locationToListing[location]:

            cursor2 = coll.find({"_id": ObjectId(listing)})

            for doc in cursor2:
                doc["Related Listings"]["Location"] = locationToListing[location]
                doc["Related Listings"]["Location"].remove(str(doc["_id"]))
                coll.update({"URL": doc["URL"]},
                            {'$set': {"Related Listings.Location": doc["Related Listings"]["Location"]}})

    print "Finished Relating Locations"


# listings may be reposted many times so it is useful to remove the duplicates before analysis
def removeDuplicates(coll):

    print "Removing Duplicate Listings..."

    cursor = coll.find()

    duplicates = set()

    for doc in cursor:

        # check if listing is a duplicate
        if str(doc["_id"]) in duplicates:                   # will remove all duplicate nodes
            coll.remove({"_id": doc["_id"]})

        else:
            # check for more duplicate listings
            if len(doc["Related Listings"].keys()) > 0:

                numKeys = len(doc["Related Listings"])
                randomKey = None

                masterList = []
                for key in doc["Related Listings"]:
                    if doc["Related Listings"][key] is not None:
                        masterList += doc["Related Listings"][key]
                        randomKey = key

                if randomKey is not None:                                              # cycle through one of the adjacency lists
                    for listing in doc["Related Listings"][randomKey]:                 # to check if there are any listings where
                        if masterList.count(listing) == numKeys and numKeys >= 3:      # all attributes of the listing are the same
                            duplicates.add(str(listing))

    cursor = coll.find()

    for doc in cursor:
        # remove duplicate listings from related Listings
        for key in doc["Related Listings"]:
            if doc["Related Listings"][key] is not None:
                copy = doc["Related Listings"][key]
                for listingID in doc["Related Listings"][key]:
                    if str(listingID) in duplicates:
                        copy.remove(str(listingID))
                    if copy is None:
                        copy = []
                doc["Related Listings"][key] = copy

                coll.update({"URL": doc["URL"]}, {'$set': {"Related Listings": doc["Related Listings"]}})

    print "Finished Removing Duplicates"


def analyze(coll):
    relateSellers(coll)
    relateTitles(coll)
    relateText(coll)
    relateImages(coll)
    # removeDuplicates(coll)

client = MongoClient()
collection = client.gbp.totalAnalyzedData

removeDuplicates(collection)