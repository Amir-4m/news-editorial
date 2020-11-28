import difflib
from importlib import import_module

import requests
from requests.auth import HTTPBasicAuth
from django.conf import settings

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
        'post': f'posts/',
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
        categories = self.instance.category.all()

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
            categories=[cat.word_press_id for cat in categories],

            # tags= , (list|int)
            # date=self.instance.created_time.__str__(),
            # terms=''
            # parent=''  # The post ID of the new post's parent.
        )
        req = self.post_request(
            self.urls['post'], json=payload_data,
            headers={'Content-Type': 'application/json'},
            auth=HTTPBasicAuth(settings.WP_USER, settings.WP_PASS)
        )
        print(req.json())
        if req.ok:
            self.instance.wp_post_id = req.json()['id']
            self.instance.status = News.STATUS_PUBLISHED
            self.instance.save()

    def update_news_from_post(self):
        req = self.post_request(
            f"{self.urls['post'] + self.instance.wp_post_id}",
            headers={'Content-Type': 'application/json'},
            auth=HTTPBasicAuth(settings.WP_USER, settings.WP_PASS)
        )
        if req.ok:
            changes = 0
            for s in difflib.ndiff(self.instance.news_main, req.json()['content']['raw']):
                if s[0] == "+" or s[0] == "-":
                    changes += 1

            self.instance.number_of_changes = changes
            self.instance.news_main_editable = req.json()['content']['raw']
            self.instance.save()
