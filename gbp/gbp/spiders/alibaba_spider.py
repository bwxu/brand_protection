import scrapy
import xlrd
from scrapy.http.request import Request
from pymongo import *

class AlibabaSpider(scrapy.Spider):
    name = "alibaba"
    allowed_domains = ["alibaba.com"]

    start_urls = []
    book = xlrd.open_workbook("Ethicon All Markeplace Data Export.xlsx")
    sheet = book.sheets()[0]
    for i in range(1, sheet.nrows):
        row = sheet.row_values(i)
        url = row[50]
        url = url.encode('ascii', 'ignore')
        url = str(url)
        if url.startswith("http://www.alibaba.com/"):
            start_urls.append(url)

    # stores data within mongodb in gbp.dataset
    client = MongoClient()
    db = client.gbp
    coll = db.alibabaRawData

    # makes sure that the collection is empty before inserting data
    coll.drop()

    # start_urls = [
    #    'http://www.alibaba.com/product-detail/Medical-Supplies-Vicryl-Suture-with-Needle_60376167087.html'
    # ]

    out = "alibabaOut.txt"
    open(out, 'w').close()

    def parse(self, response):
        with open(self.out, 'a') as f:

            # Extract important information from listing and put into listingData
            listingData = {}

            # Marketplace
            f.write("Listing Site: Alibaba\n")
            listingData["Marketplace"] = "Alibaba"

            # URL
            f.write("Listing URL: " + response.url + "\n")
            listingData["URL"] = response.url

            # Title
            title = response.xpath("//span[@class='title-text']/text()").extract()
            if len(title) == 0:                                 # page no longer exists
                return
            else:
                title = str(title[0].encode('ascii', 'ignore'))
                f.write("Listing Title: " + title + "\n")
                listingData["Title"] = title.strip()

            # Image URLs
            imageURLs = response.xpath("//ul[@class='inav util-clearfix']//div[@class='thumb']//img/@src").extract()
            f.write("Gallery Images: \n")
            imageLinks = []
            for imageURL in imageURLs:
                f.write(str(imageURL) + "\n")
                imageLinks.append(str(imageURL))
            listingData["ImageURLs"] = imageLinks

            # Price
            priceText = response.xpath("//span[@class='J-brief-info-val']//text()").extract()
            f.write("Listing Price: ")
            priceString = ""
            for text in priceText:
                text = text.encode('ascii', 'ignore')
                text = str(text)
                priceString += text
            priceString = priceString.strip()
            f.write(priceString + "\n")
            listingData["Price"] = priceString

            # Seller
            seller = response.xpath("//a[@class='company-name link-default']/@title").extract()
            seller = seller[0].encode('ascii', 'ignore')
            f.write("Seller Username: " + str(seller) + "\n")
            listingData["Seller"] = seller.strip()

            accountAge = response.xpath("//span[@class='join-year']/span[@class='value']/text()").extract()
            units = response.xpath("//span[@class='join-year']/span[@class='unit']/text()").extract()
            if len(accountAge) > 0 and len(units) > 0:
                f.write("Seller Account Age: " + str(accountAge[0]) + " " + str(units[0]) + "\n")
            else:
                f.write("Seller Account Age: \n")

            # Description Images
            descriptionImages = response.xpath("//div[@id='J-rich-text-description']//img/@src[contains(.,'.jpg')]").extract()
            f.write("Description Images: \n")
            images = []
            for imageURL in descriptionImages:
                f.write(str(imageURL) + "\n")
                images += [str(imageURL)]
            listingData["Description Image URLs"] = images

            # Description Text
            descriptionText = response.xpath("//div[@id='J-rich-text-description']//text()").extract()
            f.write("Description: \n")
            textString = ""
            for text in descriptionText:
                text = str(text.encode('ascii', 'ignore'))
                if text.isspace() or text == "":
                    continue
                text.replace("\t", "")
                textString += text.strip()
                f.write(text.strip() + "\n")
            listingData["Description Text"] = textString

            # Listing Location
            locationQuery = response.xpath("//div[@class='info-item loc-type']//span[@class='location']/text()").extract()
            location = ""
            if len(locationQuery) > 0:
                location = str(locationQuery[0].encode('ascii', 'ignore'))
            f.write("Location: " + location + "\n")
            listingData["Location"] = location.strip()

            self.insertListing(listingData)

            f.write("\n")

    # insert raw data into mongodb
    def insertListing(self, data):
        self.coll.insert(
            {
                "Marketplace" : data["Marketplace"],
                "URL" : data["URL"],
                "Title" : data["Title"],
                "ImageURLs" : data["ImageURLs"],
                "Price" : data["Price"],
                "Seller" : data["Seller"],
                "Number of Reviews" : "",
                "Review Feedback" : "",
                "Item Condition" : "",
                "Quote" : "",
                "Description URL" : "",
                "Description Image URLs" : data["Description Image URLs"],
                "Description Text" : data["Description Text"],
                "Related Listings" : {},
                "Location" : data["Location"]
            }
        )