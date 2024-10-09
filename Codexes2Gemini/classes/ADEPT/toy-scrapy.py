#  Copyright (c) 2024. Fred Zimmerman.  Personal or educational use only.  All commercial and enterprise use must be licensed, contact wfz@nimblebooks.com
import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings


class DticSpider(scrapy.Spider):
    name = 'dtic'
    allowed_domains = ['apps.dtic.mil']
    start_urls = ['https://apps.dtic.mil/sti/sitemaps.xml']
    count = 0  # Counter to track the number of documents downloaded

    def parse(self, response):
        # Extract sub-sitemap URLs from the main sitemap
        sitemap_urls = response.xpath('//sitemap/loc/text()').extract()
        for url in sitemap_urls:
            yield scrapy.Request(url, callback=self.parse_sub_sitemap)

    def parse_sub_sitemap(self, response):
        # Extract URLs from sub-sitemap and make requests to parse them
        record_urls = response.xpath('//your_xpath_for_record_urls/text()').extract()  # Replace with correct XPath
        for url in record_urls:
            if self.count < 5:  # Check if less than 5 documents have been processed
                yield scrapy.Request(url, callback=self.parse_record)

    def parse_record(self, response):
        # Increment the counter
        self.count += 1

        # Extract data from each record (assuming the document content is directly accessible)
        document_content = response.text  # or use response.body for binary data
        print(document_content)  # Print the document content

        # Stop the spider after 5 documents
        if self.count >= 5:
            self.crawler.engine.close_spider(self, 'Downloaded 5 documents')


if __name__ == "__main__":
    # Create a CrawlerProcess with Scrapy settings
    process = CrawlerProcess(get_project_settings())

    # Start the spider
    process.crawl(DticSpider)
    process.start()
