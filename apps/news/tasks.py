from datetime import timedelta
from django.utils import timezone
from celery import shared_task

from .utils import CrawlerDynamically, WordPressHandler
from .models import News


@shared_task
def collect_news_task(website_name):
    # Crawling the news website by get dynamically it
    CrawlerDynamically(website_name)()


@shared_task
def update_published_news():
    for news in News.objects.filter(
        updated_time__lte=timezone.now() - timedelta(minutes=1)
    ).exclude(
        wp_post_id=''
    ):
        WordPressHandler(news).update_news_from_post()

