import scrapy
import xlrd
from scrapy.http.request import Request
from pymongo import *


class MercadoLibreSpider(scrapy.Spider):
    name = "mercadoLibre"
    allowed_domains = ["articulo.mercadolibre.com"]

    start_urls = []
    book = xlrd.open_workbook("Ethicon All Markeplace Data Export.xlsx")
    sheet = book.sheets()[0]
    for i in range(1, sheet.nrows):
        row = sheet.row_values(i)
        url = row[50]
        url = url.encode('ascii', 'ignore')
        url = str(url)
        if "http://articulo.mercadolibre.com.ar/" in url:
            start_urls.append(url)

    # stores data within mongodb in gbp.dataset
    client = MongoClient()
    db = client.gbp
    coll = db.mercadoLibreRawData

    # makes sure that the collection is empty before inserting data
    coll.drop()

    # start_urls = [
    #    'http://articulo.mercadolibre.com.ar/MLA-597491791-ethicon-enseal-laparoscopico-5-mm-35-cm-nslg2s35-_JM',
    #    'http://articulo.mercadolibre.com.ar/MLA-597488811-pinza-harmonic-ace-ref-ace36e-ethicon-_JM',
    #    'http://articulo.mercadolibre.com.ar/MLA-596362064-malla-de-prolene-polipropileno-15-x-15-importada-_JM',
    #    'http://articulo.mercadolibre.com.co/MCO-419010741-suturas-vicryl-_JM'
    # ]

    out = "mercadoLibreOut.txt"
    open(out, 'w').close()

    def parse(self, response):
        with open(self.out, 'a') as f:

            # Extract important information from listing and put into listingData
            listingData = {}

            # Marketplace
            f.write("Listing Site: Mercado Libre\n")
            listingData["Marketplace"] = "Mercado Libre"

            # URL
            originalURL = response.url
            f.write("Listing URL: " + originalURL + "\n")
            listingData["URL"] = originalURL

            # Title
            title = response.xpath("//header[@class='bg-great-info']/h1[@itemprop='name']/text()").extract()
            if len(title) == 0:         # page has been deleted
                f.write("The listing page no longer exists\n\n")
                return
            title = title[0].encode('ascii', 'ignore')
            f.write("Listing Title: " + str(title) + "\n")
            listingData["Title"] = str(title).strip()

            # Image URLs
            imageURLs = response.xpath("//figure[@id='gallery_dflt']//img/@src[contains(.,'.jpg')]").extract()
            f.write("Gallery Images: \n")
            imageLinks = []
            for imageURL in imageURLs:
                f.write(str(imageURL) + "\n")
                imageLinks += [imageURL]
            listingData["ImageURLs"] = imageLinks

            # Price
            price = response.xpath("//article[contains(@class, 'price ch-price ')]/strong/text()").extract()
            price = str(price[0].encode('ascii', 'ignore')).strip()
            f.write("Price: " + price + "\n")
            listingData["Price"] = price

            # Seller
            seller = response.xpath("//a[@class='more-info'][@rel='nofollow']/@href").extract()[0]
            seller = str(seller).replace("http://perfil.mercadolibre.com.ar/", "")      # remove the link before the seller
            f.write("Seller: " + seller + "\n")
            listingData["Seller"] = seller.strip()

            # Feedback
            rating = response.xpath("//ol[@class='reputation-scale']/li/@class[contains(.,'selected')]").extract()
            if len(rating) > 0:
                rating = rating[0]
                rating = str(rating).replace("selected", "")
                rating = rating.replace("level-", "")
                rating = rating.strip()
                f.write("Seller Rating: " + rating + " (1 is worst and 5 is best)\n")
                listingData["Feedback"] = rating + "/5"
            else:
                listingData["Feedback"] = ""
                f.write("Seller Rating: N/A\n")

            # Description Images
            descriptionImages = response.xpath("//div[@id='description']//img/@data-src-original[contains(.,'.jpg')]").extract()
            imageList = []
            f.write("Description Images: \n")
            for image in descriptionImages:
                f.write(str(image) + "\n")
                imageList += [str(image)]
            listingData["Description Image URLs"] = imageList
            f.write("Description Text: " + "\n")

            # Description Text
            descriptionText = response.xpath("//div[@id='description']//text()").extract()
            textString = ""
            for text in descriptionText:
                if text == " " or text == "\t":
                    continue
                text = text.encode('ascii', 'ignore')
                textString += str(text).strip() + " "
                f.write(str(text).strip() + "\n")
            listingData["Description Text"] = textString

            # Listing Location
            locationQuery = response.xpath("//dl[@class='item-data']//dd//span[@class='where']/text()").extract()
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
                "Review Feedback" : data["Feedback"],
                "Item Condition" : "",
                "Quote" : "",
                "Description URL" : "",
                "Description Image URLs" : data["Description Image URLs"],
                "Description Text" : data["Description Text"],
                "Related Listings" : {},
                "Location" : data["Location"]
            }
        )