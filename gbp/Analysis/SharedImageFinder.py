from pymongo import *
import distance
import httplib2
import cStringIO
import urllib
from PIL import Image

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


def findSimilarImages(collection, url1, url2):

    cursor1 = collection.find({"URL": url1})
    cursor2 = collection.find({"URL": url2})

    hash1 = []
    hash2 = []

    docOne = None

    for doc in cursor1:
        docOne = doc

    hashToImage1 = {}

    if "ImageURLs" in docOne:
        for imageURL in docOne["ImageURLs"]:
            imghash = dHashImage(imageURL)
            if imghash != 1:
                hashToImage1[imghash] = imageURL

    if "Description Image URLs" in docOne:
        for imageURL in docOne["Description Image URLs"]:
            imghash = dHashImage(imageURL)
            if imghash != 1:
                hashToImage1[imghash] = imageURL

    docTwo = None

    for doc2 in cursor2:
        docTwo = doc2

    hashToImage2 = {}

    defaultHash = dHashImage("http://i.ebayimg.com/images/g/yGgAAOxyWmxSUwkf/s-l500.jpg")

    if "ImageURLs" in docTwo:
        for imageURL in docTwo["ImageURLs"]:
            imghash = dHashImage(imageURL)
            if imghash != 1:
                hashToImage2[imghash] = imageURL

    if "Description Image URLs" in docTwo:
        for imageURL in docTwo["Description Image URLs"]:
            imghash = dHashImage(imageURL)
            if imghash != 1:
                hashToImage2[imghash] = imageURL

    print "Shared Images:"

    for key1 in hashToImage1:
        for key2 in hashToImage2:
            if distance.levenshtein(key1, key2) <= 2:
                print (hashToImage1[key1], hashToImage2[key2])

client = MongoClient()
collection = client.gbp.test
findSimilarImages(collection,
                  "http://www.ebay.com/itm/Ethicon-Small-Liga-Clip-Applier-7-5-/141852964188",
                  "http://www.ebay.com/itm/Lane-10-1-2-LIGACLIP-Applier-NEW-/141859832232")