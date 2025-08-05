from DataCollection.Crawler.JobCrawer import Crawler

if __name__ == "__main__":
    crawler = Crawler(site_name="wanted")
    crawler.run()
