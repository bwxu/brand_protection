# brand_protection
First, go run the spiders using scrapy by calling on command line"scrapy crawl [site]" 
where [site] is ebay, alibaba, mercadoLibre.
Next, put the raw data together into one mongo collection.
Then, go to the analysis folder and run AnalyzeRawData.py on the raw data by calling the 
analyze() function on the collection.
Finally, use CreateNetwork.py to create a Gephy network and run Gephy to see the 
visualization.

