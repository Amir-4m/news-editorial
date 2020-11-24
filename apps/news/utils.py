from base64 import b64encode, b64decode
from importlib import import_module

from django.conf import settings

import requests
from requests.auth import HTTPBasicAuth

from .models import News


def CrawlerDynamically(class_name):
    """
    Args:
        class_name: 'capitalize of class_name value that equal to web site news name' + 'Crawler class name'
        to get it from "news.crawler"
    Returns: Crawler Class
    """
    module = import_module('apps.news.crawler')
    return getattr(module, f'{class_name.upper()}Crawler')


class WordPressHandler:
    base_url = 'https://www.chapar.news/wp-json/wp/v2/'
    urls = {
        'create-post': f'posts/',
        'update-post': f'posts/'
    }

    def __init__(self, instance: News):
        """
        Args:
            instance: Instance is News object.
        """
        self.instance = instance

    # def get_headers(self):
        # return dict(Authorization=f"Bearer {settings.WORDPRESS_TOKEN}")
        # return dict(Authorization="Basic %s" % b64encode('m.rezaei:09VqT4X1dxJOwB'))

    def post_request(self, url, method='post', **kwargs):
        return requests.request(method, f"{self.base_url + url}", **kwargs)

    def create_post(self):
        categories = [cat.title for cat in self.instance.category.all()]
        payload_data = dict(
            title=self.instance.news_title,
            content=self.instance.news_main,
            slug=self.instance.news_title,
            author=9,
            publicize=False,  # True or false if the post be publicized to external services.
            status='draft',  # publish, private, draft, pending, future, auto-draft
            sticky=False,  # False: (default) Post is not marked as sticky.
            password='',
            format='standard',
            media_urls=[self.instance.news_image],
            publicize_message=categories

            # date=self.instance.created_time.__str__(),
            # categories=categories,  # (list|str) Comma-separated list or array of category names
            # tags=categories,
            # terms=''
            # parent=''  # The post ID of the new post's parent.
        )
        req = self.post_request(
            self.urls['create-post'], json=payload_data,
            headers={'Content-Type': 'application/json'},
            auth=HTTPBasicAuth('m.rezaei', '09VqT4X1dxJOwB')
        )
        print(req.json())
        if req.ok:
            self.instance.wp_post_id = req.json()['id']
            self.instance.save()

    def update_post(self):
        req = self.post_request(f"{self.urls['update-post'] + self.instance.wp_post_id}")
