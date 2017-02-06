# Global Brand Protection Project

Takes a list of illicit product listings on marketplaces and constructs an illicit seller network based on listing name,
listing description, listing images, and usernames

Requirements: MongoDB, scrapy, Gephy (for visualizations)

# Instructions:

## 1. Run Scrapy

First, Run the spiders using scrapy by calling on command line"scrapy crawl [site]" 
where [site] is ebay, alibaba, mercadoLibre.

## 2. Collect Data

Next, put together all scraped raw data together into one mongo collection if multiple websites were used

## 3. Analyze Data

Then, go to the analysis folder and run AnalyzeRawData.py on the raw data by calling the 
analyze() function on the collection.

## 4. Create Visualization

Finally, use CreateNetwork.py to create a Gephy network and run Gephy to see the 
visualization.

