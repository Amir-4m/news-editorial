from celery import shared_task

from .utils import CrawlerDynamically


@shared_task
def collect_news_task(website_name):
    # Crawling the news website by get dynamically it
    CrawlerDynamically(website_name)()


