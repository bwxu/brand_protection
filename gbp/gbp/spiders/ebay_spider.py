import scrapy
import xlrd
from scrapy.http.request import Request
from pymongo import *


class EbaySpider(scrapy.Spider):
    name = "ebay"
    allowed_domains = ["ebay.com", "ebaydesc.com"]

    # grabs the URL's from the excel file, which needs to be in the same folder as the code
    start_urls = []
    book = xlrd.open_workbook("Ethicon All Markeplace Data Export.xlsx")
    sheet = book.sheets()[0]
    for i in range(1, sheet.nrows):
        row = sheet.row_values(i)
        url = row[50]
        url = url.encode('ascii', 'ignore')
        url = str(url)
        if url.startswith("http://www.ebay.com/"):
            start_urls.append(url)

    # stores data within mongodb in gbp.dataset
    client = MongoClient()
    db = client.gbp
    coll = db.ebayRawData

    # makes sure that the collection is empty before inserting data
    coll.drop()

    # scrape specific urls
    # start_urls = [
    #    'http://www.ebay.com/itm/Ligaclip-Endoscopic-Applier-Medium-EL-214-/111855676803',
    #    'http://www.ebay.com/itm/New-HARMONIC-Scalpel-Hand-Piece-HP054-Ethicon-GEN4-G300-G11-Generator-/331743359848'
    #     ]

    # outputs data to a file
    out = "ebayOut.txt"             # output file
    open(out, 'w').close()          # empty the output file before writing

    def parse(self, response):
        with open(self.out, 'a') as f:

            # Extract important information from listing and put into listingData
            listingData = {}

            # Marketplace
            f.write("Listing Site: Ebay\n")
            listingData["Marketplace"] = "Ebay"

            # URL
            originalURL = response.url
            f.write("Listing URL: " + originalURL + "\n")
            listingData["URL"] = originalURL

            # Listing Title
            title = response.xpath("//h1[@class='it-ttl'][@id='itemTitle']/text()").extract()
            if len(title) == 0:                                 # page no longer exists
                return
            else:
                title = str(title[0].encode('ascii', 'ignore'))
                f.write("Listing Title: " + str(title) + "\n")
                listingData["Title"] = title

            # Image URLs
            imageURLs = response.xpath("//div[@id='mainImgHldr']//img[@id='icImg']/@src").extract()
            f.write("Gallery Images: \n")
            imageLinks = []
            for imageURL in imageURLs:
                f.write(str(imageURL) + "\n")
                imageLinks.append(str(imageURL))
            listingData["ImageURLs"] = imageLinks

            # Price
            price = response.xpath("//span[@id='prcIsum']/text()").extract()
            priceString = ""
            if len(price) > 0:                                                      # not auction
                f.write("Listing Price: " + str(price[0]).strip() + "\n")
                priceString = str(price[0]).strip()
            else:                                                                   # auction
                price2 = response.xpath("//span[@class='notranslate vi-VR-cvipPrice']/text()").extract()
                if len(price2) > 0:
                    f.write("Listing Price: " + str(price2[0]).strip() + "\n")
                    priceString = str(price2[0]).strip()
                else:
                    f.write("Listing Price: ")
            listingData["Price"] = priceString

            # Seller
            sellerUsername = response.xpath("//span[@class='mbg-nw']/text()").extract()
            sellerString = str(sellerUsername[0])
            f.write("Seller Username: " + sellerString + "\n")
            listingData["Seller"] = sellerString

            # Number of Reviews
            numberOfReviews = response.xpath("//span[@class='mbg-l']//a/text()").extract()
            numReviews = str(numberOfReviews[0])
            f.write("Number of Reviews: " + numReviews + "\n")
            listingData["Number of Reviews"] = numReviews

            # Feedback
            reviewFeedback = response.xpath("//div[@id='si-fb']/text()").extract()
            feedback = ""
            if len(reviewFeedback) > 0:
                feedback = str(reviewFeedback[0].replace(u'\xa0', u' '))            # replace &nbsp with a space
                f.write("Review Feedback: " + feedback + "\n")
            else:                                                                   # feedback not on page
                f.write("Review Feedback: " + "\n")
            listingData["Review Feedback"] = feedback

            # Item Condition
            itemCondition = response.xpath("//div[@id='vi-itm-cond']/text()").extract()
            f.write("Item Condition: " + str(itemCondition[0]) + "\n")
            listingData["Item Condition"] = str(itemCondition[0])

            # Quote
            listingQuote = response.xpath("//span[@class='topItmCndDscMsg']/text()").extract()
            quoteString = ""
            if len(listingQuote) > 0:
                quoteString = str(listingQuote[0].encode('ascii', 'ignore'))
                f.write("Listing Quote: " + quoteString + "\n")
            else:                                                                   # quote not on page
                f.write("Listing Quote: \n")
            listingData["Quote"] = quoteString

            # Listing Location
            locationQuery = response.xpath("//div[@class='vi-cviprow']//div[@class='u-flL']/text()").extract()
            location = ""
            if len(locationQuery) > 0:
                location = str(locationQuery[0].encode('ascii', 'ignore'))
            else:                                                                   # location in a different place on page
                locationQuery2 = response.xpath("//div[@class='u-flL iti-w75 ']//div[@class='iti-eu-bld-gry ']/text()").extract()
                if len(locationQuery2) > 0:
                    location = str(locationQuery2[0].encode('ascii', 'ignore'))
            f.write("Location: " + location + "\n")
            listingData["Location"] = location

            # Description URL - Ebay listing descriptions can be accessed by following a specific URL
            description = response.xpath("//iframe[@id='desc_ifr']/@src").extract()
            if len(description) > 0:
                descriptionURL = description[0].encode('ascii', 'ignore')
                f.write("Description URL: " + str(descriptionURL) + "\n")
                f.write("\n")
                newRequest = Request(str(description[0]), callback=self.parse_page)
                listingData["Description URL"] = str(description[0])
                self.insertListing(listingData)
                return newRequest
            else:
                f.write("Description URL: \n")
                listingData["Description URL"] = ""

            self.insertListing(listingData)

            f.write("\n")

    def parse_page(self, response):
        with open(self.out, 'a') as f:

            descriptionData = {}

            originalURL = response.url
            f.write("OriginalURL: " + originalURL.strip() + "\n")
            descriptionData["Description URL"] = originalURL

            # Description Images
            imageURLs = response.xpath("//img/@src[contains(.,'.jpg')]").extract()
            f.write("Image URLs: \n")
            imageList = []
            for imageURL in imageURLs:
                f.write(str(imageURL) + "\n")
                imageList += [str(imageURL)]
            descriptionData["Description Image URLs"] = imageList

            # Description Text
            allText = response.xpath("//body//text()[not(ancestor::script|ancestor::style|ancestor::noscript)]").extract()
            f.write("Description: \n")
            textString = ""
            for text in allText:
                text = str(text.encode('ascii', 'ignore'))
                if text.isspace() or text == "":
                    continue
                text = text.replace("\t", "").strip()
                f.write(text + "\n")
                textString += " "
                textString += text
            descriptionData["Description Text"] = textString
            f.write("\n")

            self.insertDescription(descriptionData)

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
                "Number of Reviews" : data["Number of Reviews"],
                "Review Feedback" : data["Review Feedback"],
                "Item Condition" : data["Item Condition"],
                "Quote" : data["Quote"],
                "Description URL" : data["Description URL"],
                "Description Image URLs" : [],
                "Description Text" : "",
                "Related Listings" : {},
                "Location" : data["Location"]
            }
        )


    # add data about description to the relevant listing
    def insertDescription(self, data):
        self.coll.update(                                           # works because description is crawled after listing
            {"Description URL" : data["Description URL"]},
            {
                '$set' :
                    {
                        "Description Image URLs" : data["Description Image URLs"],
                        "Description Text" : data["Description Text"]
                    }
            }
        )